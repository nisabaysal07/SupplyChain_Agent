"""
*_download.py betiklerinin ortak kodu: .env okuma, YAML okuma, veritabanı bağlantısı
ve upsert (varsa güncelle, yoksa ekle).

Klasör yapısı:
    SupplyChain_Agent/
        .env
        db/
            yaml_db.py, *_download.py, download_all.py
            yaml/   ← *.yaml dosyaları

Eşleştirme kuralı:
  - YAML satırında `id` varsa satır id ile eşleştirilir (id aynıysa güncellenir).
  - `id` yoksa tablonun doğal anahtarıyla eşleştirilir (ör. countries.iso_code);
    doğal anahtarı olmayan tablolarda yeni satır olarak eklenir.
Her çalıştırma tek transaction'dır: hata olursa hiçbir değişiklik kaydedilmez.
"""

import os
import sys
from pathlib import Path

import psycopg2
import yaml

BASE_DIR = Path(__file__).resolve().parent      # .../SupplyChain_Agent/db
YAML_DIR = BASE_DIR / "yaml"                    # .../SupplyChain_Agent/db/yaml
ENV_PATHS = (BASE_DIR.parent / ".env", BASE_DIR / ".env")


def load_env() -> None:
    """Basit .env okuyucu (ek paket gerektirmez). Ortamda zaten olan değerleri ezmez."""
    for path in ENV_PATHS:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_yaml(filename: str, key: str) -> list[dict]:
    path = YAML_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"YAML dosyası bulunamadı: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    rows = data.get(key) or []
    print(f"{filename}: {len(rows)} kayıt okundu.")
    return rows


def connect():
    load_env()
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def require(row: dict, fields: tuple, n: int) -> None:
    missing = [f for f in fields if row.get(f) is None]
    if missing:
        raise ValueError(f"{n}. kayıtta eksik alan: {', '.join(missing)}")


def lookup(cur, sql: str) -> dict:
    """İki sütunlu sorguyu {anahtar: id} sözlüğüne çevirir (YAML'daki kod/ad → id)."""
    cur.execute(sql)
    return {k: v for k, v in cur.fetchall()}


def resolve(mapping: dict, value, what: str, n: int):
    """YAML'daki kodu/adı veritabanındaki id'ye çevirir; bulunamazsa açık hata verir."""
    if value is None:
        return None
    if value not in mapping:
        raise ValueError(f"{n}. kayıt: {what} bulunamadı: {value!r}")
    return mapping[value]


def upsert(cur, table: str, row: dict, natural_key: tuple | None = None) -> bool:
    """Tek satırı kaydeder. True = eklendi, False = güncellendi."""
    cols = list(row.keys())
    if row.get("id") is not None:
        conflict = ("id",)
    else:
        if "id" in cols:
            cols.remove("id")
        conflict = natural_key

    col_sql = ", ".join(cols)
    val_sql = ", ".join(f"%({c})s" for c in cols)
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({val_sql})"
    if conflict:
        updates = [c for c in cols if c not in conflict]
        set_sql = ", ".join(f"{c} = EXCLUDED.{c}" for c in updates)
        action = f"DO UPDATE SET {set_sql}" if updates else "DO NOTHING"
        sql += f" ON CONFLICT ({', '.join(conflict)}) {action}"
    sql += " RETURNING (xmax = 0)"

    cur.execute(sql, {c: row[c] for c in cols})
    result = cur.fetchone()
    return bool(result[0]) if result else False


def fix_sequence(cur, table: str) -> None:
    """SERIAL sayacını en büyük id'nin bir fazlasına çeker; sonradan id'siz eklenen satırlar çakışmaz."""
    cur.execute(
        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
        f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
    )


def sync_table(cur, table: str, prepare, natural_key: tuple | None,
               yaml_file: str, yaml_key: str) -> tuple[int, int]:
    """
    YAML'ı okur, her satırı `prepare(cur, row, n, ctx)` ile tablo sütunlarına çevirir
    ve verilen cursor üzerinden kaydeder. Commit etmez. (eklenen, güncellenen) döner.
    """
    rows = load_yaml(yaml_file, yaml_key)
    inserted = updated = 0
    ctx = {}
    for n, raw in enumerate(rows, 1):
        record = prepare(cur, raw, n, ctx)
        if upsert(cur, table, record, natural_key):
            inserted += 1
        else:
            updated += 1
    fix_sequence(cur, table)
    print(f"{table}: {inserted} eklendi, {updated} güncellendi.")
    return inserted, updated


def run(*loaders) -> None:
    """
    Verilen `load(cur)` fonksiyonlarını sırayla, tek bağlantı ve tek transaction içinde çalıştırır.
    Herhangi birinde hata olursa tümü geri alınır.
    """
    conn = connect()
    try:
        with conn:  # başarılıysa commit, hata olursa rollback
            with conn.cursor() as cur:
                for load in loaders:
                    load(cur)
    finally:
        conn.close()


def main(*loaders) -> None:
    """Betiklerin `if __name__ == "__main__"` bloğunda kullanılır: hatayı okunur şekilde basar."""
    try:
        run(*loaders)
    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr)
        print("Hiçbir değişiklik kaydedilmedi.", file=sys.stderr)
        sys.exit(1)
