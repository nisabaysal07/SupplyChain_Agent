"""
yaml/country.yaml → countries tablosu.

Çalıştırma:  python country_download.py   (ya da hepsi için: python download_all.py)
id yoksa `iso_code` ile eşleştirilir.
"""
from yaml_db import main, require, sync_table


def prepare(cur, r, n, ctx):
    require(r, ("iso_code", "name_tr", "name_en", "has_trade_agreement"), n)
    iso = str(r["iso_code"]).strip().upper()
    if len(iso) != 3:
        raise ValueError(f"{n}. kayıt: geçersiz iso_code {iso!r} (3 harf olmalı)")
    if not isinstance(r["has_trade_agreement"], bool):
        raise ValueError(f"{n}. kayıt ({iso}): has_trade_agreement true/false olmalı")
    return {
        "id": r.get("id"),
        "iso_code": iso,
        "name_tr": r["name_tr"],
        "name_en": r["name_en"],
        "has_trade_agreement": r["has_trade_agreement"],
    }


def load(cur):
    return sync_table(cur, "countries", prepare, ("iso_code",), "country.yaml", "countries")


if __name__ == "__main__":
    main(load)
