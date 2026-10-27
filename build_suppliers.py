"""
Supplier Data Builder Script:
Merges raw CSV tables from TedarikciSetiYeni/TedarikciSetiYeni/ into a single unified JSON file (suppliers.json).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "suppliers.json"

# Folders searched for the dataset CSV files, in order.
# The dataset currently lives in TedarikciSetiYeni/TedarikciSetiYeni/ (nested folder).
RAW_CANDIDATES = [
    HERE / "TedarikciSetiYeni" / "TedarikciSetiYeni",
    HERE / "TedarikciSetiYeni",
    HERE / "raw",
]


def find_raw_dir() -> Path:
    """Return the first candidate folder that contains the dataset (parcalar.csv)."""
    for folder in RAW_CANDIDATES:
        if (folder / "parcalar.csv").exists():
            return folder
    searched = "\n  ".join(str(f) for f in RAW_CANDIDATES)
    raise SystemExit(f"[!] Dataset not found (parcalar.csv). Searched:\n  {searched}")


RAW = find_raw_dir()

COMPANY = {
    "name": "KurguTek Bilgisayar A.S. (fictional)",
    "sector": "Desktop PC manufacturer assembling 10,000 computers a year from imported components",
    "city": "Ankara",
    "country": "Turkey",
}

# Part name translations: Turkish -> (English singular, English plural)
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

# Country translations: Turkish name or ISO3 code -> English name
COUNTRY_EN = {
    "Malezya": "Malaysia", "MYS": "Malaysia",
    "Güney Kore": "South Korea", "KOR": "South Korea",
    "Tayvan": "Taiwan", "TWN": "Taiwan",
    "Çin": "China", "CHN": "China",
    "Vietnam": "Vietnam", "VNM": "Vietnam",
    "Tayland": "Thailand", "THA": "Thailand",
    "Endonezya": "Indonesia", "IDN": "Indonesia",
    "Japonya": "Japan", "JPN": "Japan",
    "Amerika Birleşik Devletleri": "United States", "USA": "United States",
    "Avusturya": "Austria", "AUT": "Austria",
    "Türkiye": "Turkey", "TUR": "Turkey",
}

NONE_VALUES = {"", "yok", "aktarma yok", "-", "—"}


def read_table(name: str) -> list[dict]:
    """Read a semicolon-delimited CSV table with UTF-8 BOM encoding."""
    path = RAW / f"{name}.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f, delimiter=";")]


def by_id(rows: list[dict], key: str) -> dict:
    """Index a list of dictionaries by a specific identifier key."""
    return {r[key]: r for r in rows}


def value(v: str | None) -> str | None:
    """Normalize null or placeholder values to None."""
    return None if (v or "").strip().lower() in NONE_VALUES else v.strip()


def country_en(v: str | None) -> str | None:
    """Translate country names into English."""
    v = value(v)
    if v is None:
        return None
    if v not in COUNTRY_EN:
        print(f"  ! Warning: Country could not be translated, used as-is: {v}")
    return COUNTRY_EN.get(v, v)


def build() -> list[dict]:
    """Merge raw tables into a structured list of supplier records."""
    parts = by_id(read_table("parcalar"), "parca_id")
    firms = by_id(read_table("firmalar"), "firma_id")
    countries = by_id(read_table("ulkeler"), "ulke_id")
    routes = by_id(read_table("rotalar"), "tedarikci_id")

    out = []
    for t in read_table("tedarikciler"):
        sid = t["tedarikci_id"]
        part = parts[t["parca_id"]]
        firm = firms[t["firma_id"]]
        origin = countries[t["mense_ulke_id"]]
        route = routes.get(sid, {})
        origin_en = country_en(origin["ulke_adi"])
        assembly = country_en(t.get("birlestirme_ulke"))
        part_en, part_plural = PART_EN.get(part["parca_adi"], (part["parca_adi"], part["parca_adi"]))
        out.append({
            "id": sid,
            "name": firm["firma_adi"],
            "part": part["parca_adi"],
            "part_en": part_en,
            "part_plural_en": part_plural,
            "hs6": part.get("hs6"),
            "origin_country": origin_en,
            "assembly_countries": [assembly] if assembly and assembly != origin_en else [],
            "trade_agreement_with_turkey": origin.get("anlasma_durumu") == "1",
            "transport_mode": {"deniz": "sea", "hava": "air"}.get(route.get("tasima_modu"), route.get("tasima_modu")),
            "departure_point": value(route.get("cikis_noktasi")),
            "transit_point": value(route.get("aktarma_noktasi")),
            "arrival_point": value(route.get("varis_noktasi")),
        })
    return out


def main():
    suppliers = build()
    OUT.write_text(json.dumps({
        "_note": f"Generated from {RAW.relative_to(HERE).as_posix()}/*.csv by build_suppliers.py. Do not edit manually.",
        "company": COMPANY,
        "suppliers": suppliers,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Dataset folder: {RAW}")
    print(f"{len(suppliers)} suppliers -> {OUT}")
    for s in suppliers:
        print(f"  {s['id']:>2} {s['name']:<14} {s['part']:<12} {s['origin_country']:<12} "
              f"{s['transport_mode']:<4} {s['departure_point']} -> {s['arrival_point']}")


if __name__ == "__main__":
    main()