"""
yaml/rate_source.yaml → rate_sources tablosu.

Çalıştırma:  python rate_source_download.py   (ya da hepsi için: python download_all.py)
id yoksa `name` ile eşleştirilir (name benzersizdir).
"""
from yaml_db import main, require, sync_table


def prepare(cur, r, n, ctx):
    require(r, ("name",), n)
    return {"id": r.get("id"), "name": str(r["name"]).strip(), "url": r.get("url")}


def load(cur):
    return sync_table(cur, "rate_sources", prepare, ("name",), "rate_source.yaml", "rate_sources")


if __name__ == "__main__":
    main(load)
