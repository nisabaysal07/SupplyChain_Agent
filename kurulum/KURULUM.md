# supply_db kurulumu (takım arkadaşının bilgisayarı)

Projedeki `kurulum/` klasörü, `supply_db` veritabanının birebir kopyasını kurmak için gereken her şeyi içerir.
Python gerekmez; yalnızca **Docker Desktop** (ve projeyi çekmek için Git) kurulu olmalı.

| Dosya | Ne işe yarar |
|---|---|
| `docker-compose.yml` | PostgreSQL 17 ve Qdrant konteynerlerini başlatır |
| `.env.example` | Parola ayarları için örnek (`.env` olarak kopyalanır) |
| `supply_db.sql` | Veritabanının tam kopyası (16 tablo, tüm veri) |

## 1. Klasörü hazırla

1. Projeyi bilgisayarına çek ve `kurulum` klasörüne gir:

   ```powershell
   git clone https://github.com/nisabaysal07/SupplyChain_Agent.git
   ```

   ```powershell
   cd SupplyChain_Agent\kurulum
   ```

2. `kurulum` klasöründeki `.env.example` dosyasını `.env` adıyla kopyala ve içindeki iki değeri kendi seçtiğin değerlerle değiştir:
   - `POSTGRES_PASSWORD` — veritabanı yönetici parolası
   - `QDRANT_API_KEY` — herhangi bir uzun rastgele metin

## 2. Konteynerleri başlat

`kurulum` klasörünün içinde PowerShell açıp:

```powershell
docker compose up -d
```

`docker ps` çıktısında `proje_postgres` satırı `(healthy)` olana kadar ~10 saniye bekle.

> Hata alırsan: `proje_postgres` adında başka bir konteyner varsa veya 5432 portu doluysa
> (bilgisayarda kurulu başka bir PostgreSQL), `docker-compose.yml` içinde `"5432:5432"` satırını
> `"5433:5432"` yap; bağlantılarda port 5433 olur.

## 3. Veriyi yükle

```powershell
docker cp supply_db.sql proje_postgres:/tmp/supply_db.sql
```

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -q -v ON_ERROR_STOP=1 -f /tmp/supply_db.sql
```

Kontrol (12 çıkmalı):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT count(*) FROM locations"
```

## 4. Takım arkadaşının bağlanmasına izin ver

**a) Ona bir kullanıcı aç** (`nisa` ve parolayı değiştir):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "CREATE ROLE nisa LOGIN PASSWORD 'guclu-bir-parola'; GRANT CONNECT ON DATABASE supply_db TO nisa; GRANT USAGE ON SCHEMA public TO nisa; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nisa; GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nisa;"
```

**b) Güvenlik duvarında 5432'yi yerel ağa aç** — PowerShell'i *Yönetici olarak çalıştır*:

```powershell
New-NetFirewallRule -DisplayName "PostgreSQL 5432 (yerel ag)" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow -Profile Private -RemoteAddress LocalSubnet
```

Wi-Fi ağının profili "Özel (Private)" olmalı (Ayarlar → Ağ ve İnternet → Wi-Fi → ağın özellikleri).

**c) IP adresini öğren ve paylaş:**

```powershell
ipconfig
```

Wi-Fi bölümündeki `IPv4 Address` (ör. `192.168.1.25`) değerini; kullanıcı adı ve parolayla birlikte arkadaşına gönder.

## Bağlanan kişi için

- Host: arkadaşının IP adresi · Port: `5432` · Veritabanı: `supply_db` · Kullanıcı/parola: sana açılan
- Projenin kök klasöründeki `.env` (`SupplyChain_Agent/.env`, `kurulum/.env` değil) içinde `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD` bu değerlere ayarlanır.
- Bağlantıyı test etmek için: `Test-NetConnection <IP> -Port 5432` → `TcpTestSucceeded : True`

## Notlar

- İkiniz aynı ağda olmalısınız. Misafir Wi-Fi ağları cihazların birbirini görmesini çoğu zaman engeller.
- IP adresi modeme yeniden bağlanınca değişebilir; bağlantı koparsa `ipconfig` ile tekrar bak.
- Veritabanı yalnızca bu bilgisayar ve Docker Desktop açıkken erişilebilir.
- `db/rebuild_db.py` veritabanını silip baştan kurar; yapılan tüm değişiklikler gider. Çalıştırmadan önce ekibe haber verin.
