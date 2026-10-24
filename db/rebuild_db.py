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
  4. Yükle   : sql/supply_risk_schema.sql   → tablolar
               sql/countries_data.sql        → countries
               sql/data_inserts.sql          → suppliers, items, locations, tariffs, contracts, ...
               download_all.py (yaml/)       → countries, rate_sources, locations, items, tariffs (id ile günceller)
               sql/mock_news_data.sql        → scan_logs, articles, article_analyses, article_impacts
  5. Özet    : tablo başına satır sayısı

Veritabanı adı ve bağlantı bilgileri proje kökündeki .env'den okunur (POSTGRES_DB vb.).
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2 import sql as pgsql

import download_all
from yaml_db import BASE_DIR, load_env, run

SQL_DIR = BASE_DIR / "sql"
BACKUP_DIR = BASE_DIR / "backup"

SQL_FILES_BEFORE_YAML = ["supply_risk_schema.sql", "countries_data.sql", "data_inserts.sql"]
SQL_FILES_AFTER_YAML = ["mock_news_data.sql"]


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


def run_sql_file(db: str, filename: str) -> None:
    text = (SQL_DIR / filename).read_text(encoding="utf-8-sig")
    # Şema dosyasındaki CREATE DATABASE satırı burada atlanır (veritabanı zaten oluşturuldu)
    text = "\n".join(l for l in text.splitlines() if not l.strip().upper().startswith("CREATE DATABASE"))
    conn = psycopg2.connect(**conn_args(db))
    conn.autocommit = True  # dosyalardaki BEGIN/COMMIT kendi transaction'ını yönetir
    try:
        with conn.cursor() as cur:
            cur.execute(text)
        print(f"Yüklendi: sql/{filename}")
    except Exception as e:
        raise RuntimeError(f"sql/{filename} çalıştırılırken hata: {e}") from e
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
    for f in SQL_FILES_BEFORE_YAML:
        run_sql_file(db, f)
    run(*download_all.STEPS)
    for f in SQL_FILES_AFTER_YAML:
        run_sql_file(db, f)

    summary(db)
    print(f"\nTamamlandı: '{db}' yeni şemayla kuruldu.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nHATA: {e}", file=sys.stderr)
        sys.exit(1)
