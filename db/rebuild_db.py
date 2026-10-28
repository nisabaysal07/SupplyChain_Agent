"""
Veritabanını SIFIRDAN kurar: önce yedek alır, sonra siler, yeni şemayla yeniden oluşturur
ve tüm veriyi yükler.

Çalıştırma (proje klasöründen):
    .venv\\Scripts\\python db\\rebuild_db.py          (onay sorar)
    .venv\\Scripts\\python db\\rebuild_db.py --yes    (onay sormaz)

Adımlar:
  1. Yedek   : mevcut veritabanındaki her tablo db/backup/<tarih_saat>/<tablo>.csv olarak kaydedilir
  2. Sil     : DROP DATABASE ... (açık bağlantılar kapatılır)
  3. Oluştur : CREATE DATABASE ...
  4. Yükle   : supply_db.sql            → şema (tablolar, indeksler)
               data/01_countries.sql    → countries
               data/02_ana_veri.sql     → rate_sources, suppliers, items, locations, tariffs, contracts, ...
               data/03_haberler.sql     → scan_logs, articles, article_analyses, article_impacts
                                          (mock haberler + agent sonuçları)
  5. Özet    : tablo başına satır sayısı

Veritabanı adı ve bağlantı bilgileri proje kökündeki .env'den okunur (POSTGRES_DB vb.).
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2 import sql as pgsql

from yaml_db import BASE_DIR, load_env

SCHEMA_FILE = BASE_DIR / "supply_db.sql"
DATA_DIR = BASE_DIR / "data"          # dosyalar ad sırasıyla yüklenir (01_, 02_, ...)
BACKUP_DIR = BASE_DIR / "backup"


def conn_args(dbname: str) -> dict:
    return dict(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=dbname,
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def database_exists(db: str) -> bool:
    conn = psycopg2.connect(**conn_args("postgres"))
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def backup(db: str) -> Path | None:
    """Her tabloyu CSV olarak kaydeder. Geri yüklemek gerekirse elle COPY ... FROM ile alınabilir."""
    target = BACKUP_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    conn = psycopg2.connect(**conn_args(db))
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
            tables = [r[0] for r in cur.fetchall()]
            if not tables:
                print("Yedek: veritabanında tablo yok, yedek alınmadı.")
                return None
            target.mkdir(parents=True, exist_ok=True)
            for t in tables:
                with (target / f"{t}.csv").open("w", encoding="utf-8", newline="") as f:
                    cur.copy_expert(
                        pgsql.SQL("COPY {} TO STDOUT WITH CSV HEADER").format(pgsql.Identifier(t)), f
                    )
            # Eski şemayı da sakla (tablo yapısı)
            cur.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            with (target / "_columns.txt").open("w", encoding="utf-8") as f:
                for row in cur.fetchall():
                    f.write("\t".join(row) + "\n")
        print(f"Yedek: {len(tables)} tablo → {target}")
        return target
    finally:
        conn.close()


def recreate(db: str) -> None:
    conn = psycopg2.connect(**conn_args("postgres"))
    conn.autocommit = True  # CREATE/DROP DATABASE transaction içinde çalışmaz
    try:
        with conn.cursor() as cur:
            ident = pgsql.Identifier(db)
            # Açık bağlantıları kapat (pgAdmin, web uygulaması vb. açık olabilir)
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (db,)
            )
            cur.execute(pgsql.SQL("DROP DATABASE IF EXISTS {}").format(ident))
            print(f"Silindi: {db}")
            cur.execute(pgsql.SQL("CREATE DATABASE {}").format(ident))
            print(f"Oluşturuldu: {db}")
    finally:
        conn.close()


def run_sql_file(db: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8-sig")
    name = path.relative_to(BASE_DIR).as_posix()
    conn = psycopg2.connect(**conn_args(db))
    conn.autocommit = True  # dosyadaki BEGIN/COMMIT kendi transaction'ını yönetir
    try:
        with conn.cursor() as cur:
            cur.execute(text)
        print(f"Yüklendi: {name}")
    except Exception as e:
        raise RuntimeError(f"{name} çalıştırılırken hata: {e}") from e
    finally:
        conn.close()


def summary(db: str) -> None:
    conn = psycopg2.connect(**conn_args(db))
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
            tables = [r[0] for r in cur.fetchall()]
            print("\nTablo                 Satır")
            print("--------------------  -----")
            for t in tables:
                cur.execute(pgsql.SQL("SELECT count(*) FROM {}").format(pgsql.Identifier(t)))
                print(f"{t:<20}  {cur.fetchone()[0]:>5}")
    finally:
        conn.close()


def main() -> None:
    load_env()
    db = os.environ["POSTGRES_DB"]
    host = f"{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"

    if "--yes" not in sys.argv:
        answer = input(f"'{db}' veritabanı ({host}) SİLİNİP yeniden kurulacak. "
                       f"Önce yedek alınır. Devam edilsin mi? (e/h): ")
        if answer.strip().lower() not in ("e", "evet", "y", "yes"):
            print("İptal edildi, hiçbir şey değişmedi.")
            return

    if database_exists(db):
        backup(db)
    else:
        print(f"Yedek: '{db}' bulunamadı, yedek alınmadı.")

    recreate(db)
    run_sql_file(db, SCHEMA_FILE)
    for f in sorted(DATA_DIR.glob("*.sql")):
        run_sql_file(db, f)

    summary(db)
    print(f"\nTamamlandı: '{db}' yeni şemayla kuruldu.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nHATA: {e}", file=sys.stderr)
        sys.exit(1)
