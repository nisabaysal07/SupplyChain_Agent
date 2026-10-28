"""Builds data/suppliers.json, the supplier list the agent works with, from the project database.

    python data/build_suppliers.py      # run again whenever the supplier data changes

Each record is one supplier item (a company and the part bought from it). Its id is
supplier_items.id, so the agent's supplier ids match the database. A record holds what
the models need to match an article to a supplier: part and HS code, origin and assembly
country, trade agreement with Turkey, transport mode and the route (departure and arrival
point), taken from the shipments of the item's contracts. Identical routes are
merged; if an item has different routes, all of them are kept.

Connection settings are read from .env: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB and,
optionally, POSTGRES_HOST (default localhost) and POSTGRES_PORT (default 5432).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "suppliers.json"

COMPANY = {
    "name": "KurguTek Bilgisayar A.S. (fictional)",
    "sector": "Desktop PC manufacturer assembling 10,000 computers a year from imported components",
    "city": "Ankara",
    "country": "Turkey",
}

# Part name -> English (singular, plural)
PART_EN = {
    "İşlemci": ("CPU processor", "processors"),
    "Anakart": ("motherboard", "motherboards"),
    "Bellek": ("DDR5 memory module", "memory modules"),
    "SSD": ("SSD", "SSDs"),
    "Ekran kartı": ("graphics card", "graphics cards"),
    "Güç kaynağı": ("PC power supply", "computer power supplies"),
    "Kasa": ("PC case", "PC cases"),
    "Soğutucu": ("CPU cooler", "CPU coolers"),
    "Monitör": ("computer monitor", "computer monitors"),
}

QUERY = """
SELECT si.id, si.supplier_id, si.item_id, s.name, i.name, i.hs6, si.item_model,
       ac.name_en, sh.transport_mode, oc.name_en, oc.has_trade_agreement,
       le.name, ld.name
FROM supplier_items si
JOIN suppliers s       ON s.id = si.supplier_id
JOIN items i           ON i.id = si.item_id
LEFT JOIN countries ac ON ac.id = si.assembly_country_id
LEFT JOIN contracts c  ON c.supplier_item_id = si.id AND c.is_active
LEFT JOIN shipments sh ON sh.contract_id = c.id
LEFT JOIN countries oc ON oc.id = sh.origin_country_id
LEFT JOIN locations le ON le.id = sh.exit_location_id
LEFT JOIN locations ld ON ld.id = sh.destination_location_id
ORDER BY si.id, sh.id
"""


def load_env():
    """Loads settings from .env in this folder or in the folder above it (the repository root)."""
    for env_file in (ROOT / ".env", ROOT.parent / ".env"):
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def connect():
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )


def _one_or_list(values: list):
    """One value if all routes agree, otherwise the distinct values in order."""
    distinct = list(dict.fromkeys(v for v in values if v))
    if not distinct:
        return None
    return distinct[0] if len(distinct) == 1 else distinct


def build(rows) -> tuple[list[dict], list[str]]:
    items, warnings = {}, []
    for (sid, supplier_id, item_id, name, part, hs6, model, assembly,
         mode, origin, agreement, exit_pt, dest_pt) in rows:
        rec = items.setdefault(sid, {
            "meta": (supplier_id, item_id, name, part, hs6, model, assembly),
            "routes": [],
        })
        if mode:
            route = (mode, origin, agreement, exit_pt, dest_pt)
            if route not in rec["routes"]:
                rec["routes"].append(route)

    out = []
    for sid, rec in items.items():
        supplier_id, item_id, name, part, hs6, model, assembly = rec["meta"]
        routes = rec["routes"]
        if not routes:
            warnings.append(f"supplier item {sid} ({name}, {part}) has no active shipment; route left empty")
        if part not in PART_EN:
            warnings.append(f"no English name for part '{part}' (add it to PART_EN)")
        part_en, part_plural = PART_EN.get(part, (part, part))
        origin = _one_or_list([r[1] for r in routes])
        out.append({
            "id": str(sid),
            "supplier_id": supplier_id,
            "item_id": item_id,
            "name": name,
            "part": part,
            "part_en": part_en,
            "part_plural_en": part_plural,
            "item_model": model,
            "hs6": hs6,
            "origin_country": origin,
            "assembly_countries": [assembly] if assembly and assembly != origin else [],
            "trade_agreement_with_turkey": bool(routes) and all(r[2] for r in routes),
            "transport_mode": _one_or_list([r[0] for r in routes]),
            "departure_point": _one_or_list([r[3] for r in routes]),
            "arrival_point": _one_or_list([r[4] for r in routes]),
        })
    return out, warnings


def main():
    load_env()
    with connect() as conn:
        rows = conn.execute(QUERY).fetchall()
    suppliers, warnings = build(rows)
    OUT.write_text(json.dumps({
        "_note": "Generated by data/build_suppliers.py from the project database. Do not edit by hand; "
                 "update the database and run the script again.",
        "company": COMPANY,
        "suppliers": suppliers,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    for w in warnings:
        print("! " + w)
    print(f"{len(suppliers)} suppliers -> {OUT}")
    for s in suppliers:
        print(f"  {s['id']:>2} {s['name']:<14} {s['part']:<12} {str(s['origin_country']):<12} "
              f"{str(s['transport_mode']):<4} {s['departure_point']} -> {s['arrival_point']}")


if __name__ == "__main__":
    main()
