#!/bin/bash
# Konteyner İLK kez (boş veri klasörüyle) başlarken PostgreSQL bu betiği çalıştırır:
# önce şema (db/supply_db.sql), sonra db/data/ içindeki veri dosyaları ad sırasıyla.
# docker-compose.yml, projedeki db/ klasörünü /supply_db olarak bağlar.
set -e

for f in /supply_db/supply_db.sql /supply_db/data/*.sql; do
    echo "Yükleniyor: ${f#/supply_db/}"
    psql -v ON_ERROR_STOP=1 -q --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$f"
done
