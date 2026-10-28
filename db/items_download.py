"""
yaml/items.yaml → items tablosu.

Çalıştırma:  python items_download.py   (önce rate_sources dolu olmalı; hepsi için: python download_all.py)
Oranlar yüzde olarak yazılır (20 = %20).
source: rate_sources tablosundaki kaynağın adı (yoksa null).
id ile eşleştirilir; id yoksa yeni ürün olarak eklenir.
"""
from yaml_db import lookup, main, require, resolve, sync_table


def prepare(cur, r, n, ctx):
    if "sources" not in ctx:
        ctx["sources"] = lookup(cur, "SELECT name, id FROM rate_sources")
    require(r, ("name", "hs6", "gtip", "unit"), n)
    return {
        "id": r.get("id"),
        "name": r["name"],
        "hs6": str(r["hs6"]),
        "gtip": str(r["gtip"]),
        "unit": r["unit"],
        "kdv_rate": r.get("kdv_rate", 20),
        "otv_rate": r.get("otv_rate"),
        "kultur_fonu_rate": r.get("kultur_fonu_rate", 0),
        "gv_rate_base": r.get("gv_rate_base"),
        "igv_rate_base": r.get("igv_rate_base"),
        "source_id": resolve(ctx["sources"], r.get("source"), "kaynak", n),
        "checked_at": r.get("checked_at"),
    }


def load(cur):
    return sync_table(cur, "items", prepare, None, "items.yaml", "items")


if __name__ == "__main__":
    main(load)
