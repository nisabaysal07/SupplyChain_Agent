"""Search plan generator: produces targeted news search queries from dataset (Task 2, Step 2)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

COUNTRY_LANGUAGES = {
    "China": ["zh"], "Taiwan": ["zh-TW"], "South Korea": ["ko"], "Japan": ["ja"],
    "Thailand": ["th"], "Vietnam": ["vi"], "Malaysia": ["ms"], "Indonesia": ["id"],
    "India": ["hi"], "United States": ["en"], "Austria": ["de"], "Turkey": ["tr"],
}


def load_suppliers(path) -> tuple[list[dict], object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["suppliers"], data.get("company")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _point_en(point: str) -> str:
    """Strip parenthetical extra info from logistics point names."""
    return (point or "").split("(")[0].strip()


def rule_queries(suppliers: list[dict]) -> list[dict]:
    """Generate deterministic rule-based queries from the supplier dataset."""
    q = []

    def add(query, ids, part=None, country=None, point=None, prio="medium", reason=""):
        q.append({
            "query": query, "supplier_ids": sorted(set(ids), key=int), "part": part,
            "country": country, "logistics_point": point, "priority": prio, "reason": reason
        })

    def plural(s):
        return s.get("part_plural_en") or s.get("part_en") or s.get("part")

    by_origin = {}
    for s in suppliers:
        by_origin.setdefault(s.get("origin_country"), []).append(s)

    # 1) Import duties by supplier (part + origin country)
    for s in suppliers:
        add(f"Turkey import duty {plural(s)} {s.get('origin_country')}", [s["id"]],
            s.get("part"), s.get("origin_country"), prio="high",
            reason=f"Turkish import duties on {plural(s)} from {s.get('origin_country')}.")

    # 2) Import restrictions (quotas, bans, licensing) for all suppliers
    add("Turkey import restriction computer components", [s["id"] for s in suppliers],
        country="Turkey", reason="Turkish quotas, bans or licence rules on imported components.")

    # 3) Export restrictions by origin/assembly countries
    by_export = {}
    for s in suppliers:
        for c in dict.fromkeys([s.get("origin_country"), *s.get("assembly_countries", [])]):
            if c:
                by_export.setdefault(c, []).append(s)
    for country, group in by_export.items():
        parts = {plural(s) for s in group}
        what = parts.pop() if len(parts) == 1 else "computer components"
        add(f"{country} export restriction {what}", [s["id"] for s in group],
            country=country, reason=f"Export rules in {country} for manufactured or shipped parts.")

    # 5) Logistics points (strikes, disruptions, closures)
    points = {}
    for s in suppliers:
        for key in ("departure_point", "transit_point", "arrival_point"):
            if s.get(key):
                points.setdefault((key, s[key]), []).append(s)
    for (key, point), group in points.items():
        ids = [s["id"] for s in group]
        if key == "arrival_point":
            add(f"{_point_en(point)} Turkey strike closure", ids, country="Turkey",
                point=point, prio="high", reason=f"{len(ids)} supplier(s) arrive through this point.")
        else:
            add(f"{_point_en(point)} strike closure", ids,
                country=group[0].get("origin_country"), point=point,
                prio="high" if len(ids) > 1 else "medium",
                reason=f"{len(ids)} supplier(s) ship via this point.")

    # 6) Free trade agreements
    for country, group in by_origin.items():
        add(f"Turkey {country} free trade agreement", [s["id"] for s in group],
            country=country, prio="low", reason=f"Trade agreement changes between Turkey and {country}.")
    return q


def supplier_languages(suppliers: list[dict]) -> tuple[list[dict], list[str]]:
    """Map each supplier to its associated countries and local news languages."""
    rows, warnings = [], []
    for s in suppliers:
        countries = dict.fromkeys([s.get("origin_country"), *s.get("assembly_countries", [])])
        for c in countries:
            if not c:
                continue
            langs = COUNTRY_LANGUAGES.get(c)
            if langs is None:
                warnings.append(f"Language not defined for {c} (COUNTRY_LANGUAGES), skipped for {s['id']}")
                continue
            rows.append({"supplier_id": s["id"], "country": c, "languages": langs})
    return rows, warnings


def finalize(queries: list[dict], suppliers: list[dict]) -> tuple[list[dict], list[str]]:
    """Merge identical queries, sort by priority and coverage, and attach supplier names/products."""
    warnings, merged = [], {}
    for item in queries:
        key = item["query"].lower()
        if key in merged:
            m = merged[key]
            m["supplier_ids"] = sorted(set(m["supplier_ids"]) | set(item["supplier_ids"]), key=int)
            if PRIORITY_ORDER[item["priority"]] < PRIORITY_ORDER[m["priority"]]:
                m["priority"] = item["priority"]
            continue
        merged[key] = dict(item)

    ordered = sorted(merged.values(), key=lambda x: (PRIORITY_ORDER[x["priority"]], -len(x["supplier_ids"])))
    known = {s["id"] for s in suppliers}
    missing = sorted(known - {i for x in ordered for i in x["supplier_ids"]})
    if missing:
        warnings.append(f"Suppliers without queries: {', '.join(missing)}")
    
    by_id = {s["id"]: s for s in suppliers}
    fields = ("query", "supplier_ids", "supplier_names", "products", "part", "country",
              "logistics_point", "priority", "reason")
    out = []
    for i, x in enumerate(ordered, 1):
        x["supplier_names"] = [by_id[sid].get("name") for sid in x["supplier_ids"]]
        x["products"] = [by_id[sid].get("part") for sid in x["supplier_ids"]]
        out.append({"query_id": f"Q{i:03d}", **{k: x.get(k) for k in fields}})
    return out, warnings


def build_plan(suppliers: list[dict]) -> dict:
    queries, warnings = finalize(rule_queries(suppliers), suppliers)
    languages, lang_warnings = supplier_languages(suppliers)
    return {
        "schema_version": "1.7",
        "generated_at": _now(),
        "source": "rules",
        "supplier_count": len(suppliers),
        "query_count": len(queries),
        "warnings": warnings + lang_warnings,
        "supplier_languages": languages,
        "queries": queries,
    }


def main():
    ap = argparse.ArgumentParser(description="Generate targeted news search queries from dataset")
    ap.add_argument("--suppliers", default=str(HERE / "suppliers.json"))
    ap.add_argument("--out", default=str(HERE / "search_plan.json"))
    args = ap.parse_args()

    suppliers, _ = load_suppliers(args.suppliers)
    plan = build_plan(suppliers)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{plan['query_count']} queries, {plan['supplier_count']} suppliers")
    for q in plan["queries"]:
        print(f"  {q['query_id']} [{q['priority']:<6}] {q['query']:<52} {(q['country'] or '-'):<12} {' '.join(q['supplier_ids'])}")
    for w in plan["warnings"]:
        print("! " + w)
    print(f"Output -> {out}")


if __name__ == "__main__":
    main()