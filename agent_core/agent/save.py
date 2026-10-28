"""Stores an agent results file in the project database.

    python -m agent.save output/agent_results_<timestamp>.json

Used directly by "python -m agent --db --save", or on its own to store a results file
after checking it. For every article the agent processed without errors, one article_analyses row
is written, plus article_impacts rows for a relevant article. Each impact row names exactly one
thing (the database allows one of country, location, supplier or item per row): the country the
article names (not written when the article names only Turkey, e.g. a VAT change for every origin),
the affected ports and airports, and the item and the supplier of every affected supplier item.
So a tariff with a country row applies to that country only; one without applies to every origin.
Articles are matched by
article_id (database mode) or by URL (results from a JSON file). An article that already
has an analysis is skipped, so a file can be saved twice without creating duplicates.
Everything is written in one transaction: if any row fails, nothing is stored.
After a successful save, risk_alerts.py (repository root) refreshes cost_impacts, alerts and alert_articles.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .env import ROOT, load_env
from .news_loader import connect

FIND_ARTICLE_BY_ID = "SELECT id, last_seen_scan_id FROM articles WHERE id = %s"
FIND_ARTICLE_BY_URL = "SELECT id, last_seen_scan_id FROM articles WHERE url = %s"
HAS_ANALYSIS = "SELECT 1 FROM article_analyses WHERE article_id = %s"
ANALYSIS_COLUMNS = ["article_id", "scan_log_id", "is_relevant", "impact_score", "event_type", "summary",
                    "rate_type", "old_rate_pct", "new_rate_pct", "expected_delay_days"]
# Written only when the database has the column (added later to the schema)
OPTIONAL_COLUMNS = ["price_change_pct"]
EXISTING_COLUMNS = """
SELECT column_name FROM information_schema.columns
WHERE table_schema = current_schema() AND table_name = 'article_analyses'
"""
SUPPLIER_ITEM = "SELECT supplier_id, item_id FROM supplier_items WHERE id = %s"
COUNTRY_BY_NAME = "SELECT id FROM countries WHERE lower(name_en) = lower(%s) OR lower(name_tr) = lower(%s)"
LOCATION_BY_NAME = "SELECT id FROM locations WHERE name = %s"
INSERT_IMPACT = "INSERT INTO article_impacts (article_analysis_id, {column}) VALUES (%s, %s)"

# A measure that names no country other than Turkey applies to every origin: no country row
TURKEY = {"turkey", "türkiye", "turkiye"}


def save(results: list[dict], conn) -> tuple[int, int, list[str]]:
    """Returns (analyses written, impacts written, messages)."""
    analyses = impacts = 0
    messages = []
    existing = {name for (name,) in conn.execute(EXISTING_COLUMNS).fetchall()}
    columns = ANALYSIS_COLUMNS + [c for c in OPTIONAL_COLUMNS if c in existing]
    insert_analysis = (f"INSERT INTO article_analyses ({', '.join(columns)}) "
                       f"VALUES ({', '.join(['%s'] * len(columns))}) RETURNING id")
    for r in results:
        nid = r["news_id"]
        if r.get("errors"):
            messages.append(f"{nid}: skipped, not stored because of errors (analysed again on the next run)")
            continue

        if r.get("article_id") is not None:
            row = conn.execute(FIND_ARTICLE_BY_ID, (r["article_id"],)).fetchone()
        else:
            row = conn.execute(FIND_ARTICLE_BY_URL, (r.get("source_url"),)).fetchone()
        if row is None:
            messages.append(f"{nid}: skipped, article not found in the articles table")
            continue
        article_id, last_scan = row
        if conn.execute(HAS_ANALYSIS, (article_id,)).fetchone():
            messages.append(f"{nid}: skipped, article {article_id} already has an analysis")
            continue

        a = r.get("analysis") or {}
        values = {
            "article_id": article_id, "scan_log_id": r.get("scan_log_id") or last_scan,
            "is_relevant": r["is_relevant"], "impact_score": r["impact_score"], "event_type": r["event_type"],
            **{k: a.get(k) for k in ("summary", "rate_type", "old_rate_pct", "new_rate_pct",
                                     "expected_delay_days", "price_change_pct")},
        }
        analysis_id = conn.execute(insert_analysis, [values[c] for c in columns]).fetchone()[0]
        analyses += 1

        targets = []  # (column, id) pairs, each stored once
        supplier_ids = r.get("affected_supplier_ids", [])
        country_name = (a.get("country") or "").strip()
        if supplier_ids and country_name and country_name.lower() not in TURKEY:
            country = conn.execute(COUNTRY_BY_NAME, (country_name, country_name)).fetchone()
            if country:
                targets.append(("country_id", country[0]))
            else:
                messages.append(f"{nid}: country '{country_name}' not in the countries table, not stored")
        for name in a.get("affected_locations") or []:
            location = conn.execute(LOCATION_BY_NAME, (name,)).fetchone()
            if location:
                targets.append(("location_id", location[0]))
            else:
                messages.append(f"{nid}: location '{name}' not in the locations table, not stored")
        for sid in supplier_ids:
            row = conn.execute(SUPPLIER_ITEM, (int(sid),)).fetchone()
            if row is None:
                messages.append(f"{nid}: supplier item {sid} not found, impact not stored")
                continue
            supplier_id, item_id = row
            targets += [("item_id", item_id), ("supplier_id", supplier_id)]
        for column, value in dict.fromkeys(targets):
            conn.execute(INSERT_IMPACT.format(column=column), (analysis_id, value))
            impacts += 1
    return analyses, impacts, messages


def main():
    ap = argparse.ArgumentParser(description="Store an agent results file in the project database")
    ap.add_argument("results", help="Results file written by the agent (output/agent_results_*.json)")
    args = ap.parse_args()

    data = json.loads(Path(args.results).read_text(encoding="utf-8"))
    if data.get("run", {}).get("mock"):
        raise SystemExit("This is a dry-run file with placeholder answers; it is not stored.")

    load_env()
    store(data["results"])


def store(results: list[dict]):
    """Writes the results in one transaction and prints a short report."""
    with connect() as conn:
        analyses, impacts, messages = save(results, conn)
    # leaving the "with" block commits; an exception rolls everything back

    for m in messages:
        print("! " + m)
    print(f"Stored {analyses} analyses and {impacts} impact rows.")
    if analyses:
        update_alerts()


def update_alerts():
    """New analyses -> cost_impacts, alerts and alert_articles (risk_alerts.py in the repository root).
    The analyses are already committed, so a failure here only skips the alerts; run it later with:
    python risk_alerts.py"""
    import sys
    sys.path.insert(0, str(ROOT.parent))
    try:
        from risk_alerts import update_risks
        update_risks()
    except Exception as e:
        print(f"! Alerts not updated ({type(e).__name__}: {e}); run 'python risk_alerts.py' in the repository root")


if __name__ == "__main__":
    main()
