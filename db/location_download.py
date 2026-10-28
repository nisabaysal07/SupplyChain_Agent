"""
yaml/location.yaml → locations tablosu.

Çalıştırma:  python location_download.py   (önce countries dolu olmalı; hepsi için: python download_all.py)
country: ülkenin iso_code'u (ör. "TUR"); boğaz/kanal gibi uluslararası noktalar için null.
id yoksa `code` ile eşleştirilir; code da yoksa yeni satır eklenir.
latitude / longitude / city panel haritası içindir; bu sütunlar olmadan kurulmuş bir veritabanında
betik onları kendisi ekler (veritabanını yeniden kurmak gerekmez).
"""
from yaml_db import lookup, main, require, resolve, sync_table

TYPES = {"port", "airport", "border_gate", "chokepoint"}

# supply_db.sql ile aynı tanımlar; sütunlar zaten varsa bir şey değişmez
ADD_MAP_COLUMNS_SQL = """
ALTER TABLE locations
    ADD COLUMN IF NOT EXISTS latitude  NUMERIC(8,5) CHECK (latitude  BETWEEN -90  AND 90),
    ADD COLUMN IF NOT EXISTS longitude NUMERIC(8,5) CHECK (longitude BETWEEN -180 AND 180),
    ADD COLUMN IF NOT EXISTS city      VARCHAR(100)
"""


def prepare(cur, r, n, ctx):
    if "countries" not in ctx:
        ctx["countries"] = lookup(cur, "SELECT iso_code, id FROM countries")
    require(r, ("name", "location_type"), n)
    if r["location_type"] not in TYPES:
        raise ValueError(f"{n}. kayıt: location_type şunlardan biri olmalı: {', '.join(sorted(TYPES))}")
    country = str(r["country"]).strip().upper() if r.get("country") else None
    return {
        "id": r.get("id"),
        "name": r["name"],
        "code": r.get("code"),
        "location_type": r["location_type"],
        "country_id": resolve(ctx["countries"], country, "ülke", n),
        "latitude": r.get("latitude"),
        "longitude": r.get("longitude"),
        "city": r.get("city"),
    }


def load(cur):
    cur.execute(ADD_MAP_COLUMNS_SQL)
    return sync_table(cur, "locations", prepare, ("code",), "location.yaml", "locations")


if __name__ == "__main__":
    main(load)
