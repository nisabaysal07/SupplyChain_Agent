"""
Risk Alerts Module (Görev 3 → Görev 4):
Turns the stored news analyses into cost impacts and alerts.

Flow:  scan (main.py) → agent (article_analyses + article_impacts) → THIS → panel_sync.py / notify.py
    1. cost_impacts : maliyet_etkisi/maliyet_formulu.py is run on the latest analysis of every article
                      and the results are upserted (one row per analysis).
    2. alerts       : the relevant analyses of the articles seen in a scan are grouped into risks.
                      Risk = event_type + one target (country / location / supplier / item), the same
                      as alerts.risk_key. One open alert per risk; status per scan:
                          new        risk seen for the first time
                          changed    score / rate / delay / price changed, or a new source article
                          unchanged  still there, nothing changed
                          resolved   not seen in RESOLVE_AFTER_SCANS successful scans in a row
    3. alert_articles : every article that supports a risk is linked to its alert.

An article counts as "seen in scan S" when articles.last_seen_scan_id = S or it was analysed in S.
Running the same scan twice changes nothing (idempotent).

Importance (written to alerts):
    effect   (0.1–1) cost impact of the risk's analysis (cost_impacts):
                 cost change  → |cost_share_pct| / 5, limited to 0.1–1 (5% of the yearly part cost = 1)
                 delay        → production stops 1.0 ; stock insufficient 0.7 ; near reorder 0.5 ; sufficient 0.3
                 not calculated / no cost row → 0.5
    severity = impact_score × effect :  ≥ 60 high, ≥ 30 medium, else low
    priority_score = impact_score × effect × novelty  (new 1.0, changed 0.8, unchanged 0.5)

Usage:
    python risk_alerts.py              # latest successful scan (run after: python -m agent --db --save)
    python risk_alerts.py --scan 9     # a given scan
    python risk_alerts.py --replay     # every successful scan in order (fills the history once)
main.run_scan calls update_risks() after every successful scan.
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from scan_log import connect

HERE = Path(__file__).resolve().parent
RESOLVE_AFTER_SCANS = 3
NOVELTY = {"new": 1.0, "changed": 0.8, "unchanged": 0.5}
# alerts.panel_synced_at (panel_sync.py) is missing in a supply_db built before it was added
ADD_PANEL_COLUMN_SQL = "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS panel_synced_at TIMESTAMPTZ"

# Values compared between the alert's previous analysis and the new one
TRACKED = ("impact_score", "rate_type", "old_rate_pct", "new_rate_pct", "expected_delay_days", "price_change_pct")
TARGETS = ("supplier_id", "item_id", "location_id", "country_id")   # risk_key order
# The agent stores several targets per article (country, ports, and item + supplier of every affected
# supplier item). One level is used so one risk is not split into many cards: a port problem is one
# alert for the port (all news about it merge), a tariff or price change one alert per supplier.
LEVELS = {"transport_disruption": ("location_id", "supplier_id", "item_id", "country_id"),
          "trade_restriction": ("location_id", "supplier_id", "item_id", "country_id")}
DEFAULT_LEVELS = ("supplier_id", "item_id", "country_id", "location_id")

# Latest analysis (as of scan S) of every relevant article seen in S, with its targets
SEEN_SQL = """
WITH seen AS (
    SELECT id FROM articles WHERE last_seen_scan_id = %(scan)s
    UNION SELECT article_id FROM article_analyses WHERE scan_log_id = %(scan)s
), latest AS (
    SELECT DISTINCT ON (aa.article_id) aa.*
    FROM article_analyses aa JOIN seen ON seen.id = aa.article_id
    WHERE aa.scan_log_id <= %(scan)s
    ORDER BY aa.article_id, aa.scan_log_id DESC, aa.id DESC
)
SELECT l.id, l.article_id, l.is_relevant, l.event_type, l.impact_score, l.rate_type, l.old_rate_pct,
       l.new_rate_pct, l.expected_delay_days, l.price_change_pct, a.title,
       ai.supplier_id, ai.item_id, ai.location_id, ai.country_id
FROM latest l
JOIN articles a ON a.id = l.article_id
LEFT JOIN article_impacts ai ON ai.article_analysis_id = l.id
WHERE l.is_relevant AND l.event_type IS NOT NULL AND l.event_type <> 'not_relevant'
ORDER BY l.id
"""
ANALYSIS_SQL = f"SELECT id, {', '.join(TRACKED)} FROM article_analyses WHERE id = ANY(%s)"
COST_SQL = """SELECT article_analysis_id, status, calc_type, cost_share_pct, stock_status, stop_days, unbuilt_pc
              FROM cost_impacts WHERE article_analysis_id = ANY(%s)"""
OPEN_ALERT_SQL = """SELECT id, status, current_score, latest_analysis_id, last_seen_scan_id
                    FROM alerts WHERE risk_key = %s AND status <> 'resolved'"""
LINKED_SQL = "SELECT article_id FROM alert_articles WHERE alert_id = %s"
INSERT_ALERT_SQL = """
INSERT INTO alerts (event_type, supplier_id, item_id, location_id, country_id, status, current_score,
                    priority_score, severity, latest_analysis_id, first_seen_scan_id, last_seen_scan_id)
VALUES (%(event_type)s, %(supplier_id)s, %(item_id)s, %(location_id)s, %(country_id)s, 'new', %(score)s,
        %(priority)s, %(severity)s, %(analysis)s, %(scan)s, %(scan)s)
RETURNING id
"""
# A change makes the card unread, not notified and not synced to the panel again, so the panel shows / sends it once more.
# prev_score moves only when a new scan sees the risk, and running the same scan again keeps its
# change_reason (SET reads the old row values)
UPDATE_ALERT_SQL = """
UPDATE alerts SET status = %(status)s, current_score = %(score)s,
       change_reason = CASE WHEN last_seen_scan_id = %(scan)s AND %(reason)s::text IS NULL
                            THEN change_reason ELSE %(reason)s END,
       prev_score = CASE WHEN last_seen_scan_id = %(scan)s THEN prev_score ELSE current_score END,
       priority_score = %(priority)s, severity = %(severity)s,
       latest_analysis_id = %(analysis)s, last_seen_scan_id = %(scan)s, updated_at = now(),
       is_read     = CASE WHEN %(notify)s THEN false ELSE is_read END,
       read_at     = CASE WHEN %(notify)s THEN NULL ELSE read_at END,
       notified_at = CASE WHEN %(notify)s THEN NULL ELSE notified_at END,
       panel_synced_at = CASE WHEN %(notify)s THEN NULL ELSE panel_synced_at END
WHERE id = %(id)s
"""
LINK_SQL = """INSERT INTO alert_articles (alert_id, article_id, added_scan_id) VALUES (%s, %s, %s)
              ON CONFLICT (alert_id, article_id) DO NOTHING"""
# Open alerts whose last sighting is followed by RESOLVE_AFTER_SCANS successful scans (up to S).
# The panel gets the end date on the next sync.
RESOLVE_SQL = """
UPDATE alerts al SET status = 'resolved', resolved_scan_id = %(scan)s, updated_at = now(), panel_synced_at = NULL,
       change_reason = 'not seen in the last ' || %(n)s || ' successful scans'
WHERE al.status <> 'resolved' AND al.last_seen_scan_id < %(scan)s
  AND (SELECT count(*) FROM scan_logs s
       WHERE s.id > al.last_seen_scan_id AND s.id <= %(scan)s
         AND (s.status = 'success' OR s.id = %(scan)s)) >= %(n)s
RETURNING al.id
"""


def _num(x) -> Optional[float]:
    return None if x is None else float(x)


def effect(cost: Optional[tuple]) -> float:
    """0.1–1: how much the risk's analysis hurts the company (see the module docstring)."""
    if cost is None:
        return 0.5
    _, status, calc_type, share, stock, stop_days, unbuilt = cost
    if status != "hesaplandi":
        return 0.5
    if calc_type == "lojistik_gecikme":
        if (stop_days or 0) > 0 or (unbuilt or 0) > 0:
            return 1.0
        return {"yetersiz": 0.7, "sinira_yakin": 0.5}.get(stock, 0.3)
    return min(1.0, max(0.1, abs(float(share or 0)) / 5))


def importance(score: Optional[int], eff: float, status: str) -> tuple:
    """(priority_score, severity)."""
    base = (score or 0) * eff
    severity = "high" if base >= 60 else "medium" if base >= 30 else "low"
    return round(base * NOVELTY[status], 2), severity


def _fmt(x) -> str:
    return "-" if x is None else f"{float(x):g}" if not isinstance(x, str) else x


def changes(before: Optional[dict], after: dict) -> List[str]:
    """What differs between the alert's previous analysis and the new one, e.g. 'impact_score 58 → 72'."""
    if before is None:
        return []
    same = lambda k: before[k] == after[k] if k == "rate_type" else _num(before[k]) == _num(after[k])
    return [f"{k} {_fmt(before[k])} → {_fmt(after[k])}" for k in TRACKED if not same(k)]


def update_costs(conn) -> int:
    """Step 1: cost_impacts for the latest analysis of every article. Returns the rows written."""
    sys.path.insert(0, str(HERE / "maliyet_etkisi"))
    from maliyet_formulu import sonuclari_yaz, veritabani_analiz
    return sonuclari_yaz(conn, veritabani_analiz(conn))


def update_alerts(conn, scan_id: int) -> Dict[str, int]:
    """Step 2: alerts + alert_articles for one scan, in one transaction. Returns counts per status."""
    counts = {"new": 0, "changed": 0, "unchanged": 0, "resolved": 0, "skipped": 0}
    with conn.cursor() as cur:
        cur.execute(ADD_PANEL_COLUMN_SQL)
        cur.execute(SEEN_SQL, {"scan": scan_id})
        rows = cur.fetchall()

        # Every analysis with its targets: {analysis id: {column: {ids}}}
        analyses, targets = {}, {}
        for (aid, article, _, event, score, rate, old, new, delay, price, title, *target) in rows:
            analyses[aid] = {"id": aid, "article_id": article, "event_type": event, "impact_score": score,
                             "rate_type": rate, "old_rate_pct": old, "new_rate_pct": new,
                             "expected_delay_days": delay, "price_change_pct": price, "title": title}
            for column, value in zip(TARGETS, target):
                if value is not None:
                    targets.setdefault(aid, {}).setdefault(column, set()).add(value)

        # Group the analyses into risks: risk_key → analyses (+ the articles behind them)
        risks = {}
        for aid, a in analyses.items():
            found = targets.get(aid, {})
            column = next((c for c in LEVELS.get(a["event_type"], DEFAULT_LEVELS) if c in found), None)
            if column is None:
                counts["skipped"] += 1
                print(f"[!] Analiz {aid}: article_impacts satırı yok, alert açılamadı")
                continue
            for value in found[column]:
                key = f"{a['event_type']}:{column[:-3]}:{value}"
                risks.setdefault(key, {"event_type": a["event_type"], "column": column, "value": value,
                                       "analyses": set()})["analyses"].add(aid)

        cur.execute(COST_SQL, (list(analyses),))
        costs = {r[0]: r for r in cur.fetchall()}

        for key, risk in risks.items():
            # The card shows the strongest analysis (highest score, then the newest)
            best = max((analyses[a] for a in risk["analyses"]), key=lambda a: (a["impact_score"] or 0, a["id"]))
            articles = {analyses[a]["article_id"] for a in risk["analyses"]}
            eff = effect(costs.get(best["id"]))
            cur.execute(OPEN_ALERT_SQL, (key,))
            alert = cur.fetchone()

            if alert is None:
                priority, severity = importance(best["impact_score"], eff, "new")
                cur.execute(INSERT_ALERT_SQL, {
                    **{c: (risk["value"] if c == risk["column"] else None) for c in TARGETS},
                    "event_type": risk["event_type"], "score": best["impact_score"], "priority": priority,
                    "severity": severity, "analysis": best["id"], "scan": scan_id})
                alert_id, status = cur.fetchone()[0], "new"
            else:
                alert_id, old_status, _, old_analysis, last_seen = alert
                cur.execute(ANALYSIS_SQL, ([old_analysis],))
                prev = cur.fetchone()
                before = dict(zip(("id",) + TRACKED, prev)) if prev else None
                cur.execute(LINKED_SQL, (alert_id,))
                new_sources = articles - {r[0] for r in cur.fetchall()}
                reasons = changes(before, best)
                if new_sources:
                    titles = sorted(a["title"] for a in analyses.values() if a["article_id"] in new_sources)
                    reasons.append("new source: " + "; ".join(t[:80] for t in titles))
                same_scan = last_seen == scan_id   # running a scan again keeps its result
                if reasons:
                    status = "new" if same_scan and old_status == "new" else "changed"
                else:
                    status = old_status if same_scan else "unchanged"
                priority, severity = importance(best["impact_score"], eff, status)
                cur.execute(UPDATE_ALERT_SQL, {
                    "id": alert_id, "status": status, "reason": "; ".join(reasons) or None,
                    "score": best["impact_score"], "priority": priority, "severity": severity, "analysis": best["id"], "scan": scan_id,
                    "notify": bool(reasons)})
                if same_scan and not reasons:
                    status = None   # nothing new in this run
            for article in articles:
                cur.execute(LINK_SQL, (alert_id, article, scan_id))
            if status:
                counts[status] += 1

        cur.execute(RESOLVE_SQL, {"scan": scan_id, "n": RESOLVE_AFTER_SCANS})
        counts["resolved"] = len(cur.fetchall())
    conn.commit()
    return counts


def update_risks(scan_id: Optional[int] = None) -> Dict[str, int]:
    """Both steps for one scan (default: the latest successful one). Prints a short summary."""
    conn = connect()
    try:
        if scan_id is None:
            with conn.cursor() as cur:
                cur.execute("SELECT max(id) FROM scan_logs WHERE status = 'success'")
                scan_id = cur.fetchone()[0]
            if scan_id is None:
                print("[!] Başarılı tarama yok, alert güncellenmedi")
                return {}
        try:
            print(f"[✓] {update_costs(conn)} maliyet etkisi cost_impacts tablosuna yazıldı")
        except (ValueError, KeyError) as e:
            # Missing company data must not stop the alerts; they then use the neutral effect
            conn.rollback()
            print(f"[!] Maliyet etkisi hesaplanamadı, alert'ler maliyetsiz güncelleniyor: {e}")
        counts = update_alerts(conn, scan_id)
        print(f"[✓] Alert'ler güncellendi (scan_logs.id = {scan_id}): "
              + ", ".join(f"{k} {v}" for k, v in counts.items()))
        return counts
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Fill cost_impacts, alerts and alert_articles from the analyses.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", type=int, help="scan_logs.id to process (default: latest successful scan)")
    group.add_argument("--replay", action="store_true", help="Process every successful scan in order")
    args = parser.parse_args()
    load_dotenv(HERE / ".env")

    if not args.replay:
        update_risks(args.scan)
        return
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM scan_logs WHERE status = 'success' ORDER BY id")
            scans = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
    for scan_id in scans:
        update_risks(scan_id)


if __name__ == "__main__":
    main()
