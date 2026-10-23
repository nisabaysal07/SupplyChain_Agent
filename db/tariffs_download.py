"""
yaml/tariffs.yaml → tariffs tablosu.

Çalıştırma:  python tariffs_download.py
(önce countries, rate_sources ve items dolu olmalı; hepsi için: python download_all.py)
item_id: items tablosundaki ürünün id'si; country: menşe ülkenin iso_code'u.
source: rate_sources tablosundaki kaynağın adı (yoksa null).
valid_to: null = halen yürürlükte.
id yoksa (item_id, country, valid_from) üçlüsüyle eşleştirilir.
"""
from yaml_db import lookup, main, require, resolve, sync_table


def prepare(cur, r, n, ctx):
    if "countries" not in ctx:
        ctx["countries"] = lookup(cur, "SELECT iso_code, id FROM countries")
        ctx["sources"] = lookup(cur, "SELECT name, id FROM rate_sources")
        ctx["items"] = lookup(cur, "SELECT id, id FROM items")
    require(r, ("item_id", "country", "gv_rate", "valid_from"), n)
    return {
        "id": r.get("id"),
        "item_id": resolve(ctx["items"], r["item_id"], "ürün", n),
        "country_id": resolve(ctx["countries"], str(r["country"]).strip().upper(), "ülke", n),
        "gv_rate": r["gv_rate"],
        "igv_rate": r.get("igv_rate", 0),
        "valid_from": r["valid_from"],
        "valid_to": r.get("valid_to"),
        "source_id": resolve(ctx["sources"], r.get("source"), "kaynak", n),
        "checked_at": r.get("checked_at"),
    }


def load(cur):
    return sync_table(cur, "tariffs", prepare, ("item_id", "country_id", "valid_from"),
                      "tariffs.yaml", "tariffs")


if __name__ == "__main__":
    main(load)
