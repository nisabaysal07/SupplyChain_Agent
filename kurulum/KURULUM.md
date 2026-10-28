# supply_db kurulumu (takım arkadaşının bilgisayarı)

Projedeki `kurulum/` klasörü, `supply_db` veritabanını kurmak için gereken her şeyi içerir.
Python gerekmez; yalnızca **Docker Desktop** (ve projeyi çekmek için Git) kurulu olmalı.

| Dosya | Ne işe yarar |
|---|---|
| `docker-compose.yml` | PostgreSQL 17 ve Qdrant konteynerlerini başlatır |
| `.env.example` | Parola ayarları için örnek (`.env` olarak kopyalanır) |
| `init_db.sh` | İlk başlatmada şemayı ve veriyi otomatik yükler |

Şema ve veri `db/` klasöründen alınır, `kurulum/` içinde kopyası tutulmaz:

| Dosya | İçerik |
|---|---|
| `db/supply_db.sql` | Şema: 16 tablo ve indeksler (veri yok) |
| `db/data/01_countries.sql` | 50 ülke |
| `db/data/02_ana_veri.sql` | Tedarikçiler, ürünler, lokasyonlar, gümrük oranları, sözleşmeler, stok, sevkiyatlar |
| `db/data/03_haberler.sql` | Taramalar ve haberler (mock haberler + agent sonuçları) |

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

İlk başlatmada şema ve veri otomatik yüklenir (`db/supply_db.sql`, ardından `db/data/*.sql` ad sırasıyla).
`docker ps` çıktısında `proje_postgres` satırı `(healthy)` olana kadar ~20 saniye bekle.

> Hata alırsan: `proje_postgres` adında başka bir konteyner varsa veya 5432 portu doluysa
> (bilgisayarda kurulu başka bir PostgreSQL), `docker-compose.yml` içinde `"5432:5432"` satırını
> `"5433:5432"` yap; bağlantılarda port 5433 olur.

## 3. Veriyi kontrol et

Kontrol (11 çıkmalı):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT count(*) FROM locations"
```

Şemanın güncel olduğunu kontrol et (`price_change_pct` sütunu, 1 çıkmalı):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT count(*) FROM information_schema.columns WHERE table_name = 'article_analyses' AND column_name = 'price_change_pct'"
```

Süveyş Kanalı verisinin kaldırıldığını kontrol et (0 çıkmalı):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT count(*) FROM articles WHERE url LIKE '%suez%'"
```

0 çıkıyorsa veya tablo yok hatası alıyorsan yükleme kayıtlarına bak (`Yükleniyor: ...` satırları ve varsa hata):

```powershell
docker logs proje_postgres
```

> Otomatik yükleme **yalnızca veritabanı boşken** (ilk `docker compose up`) çalışır. Daha önce kurulmuş
> bir veritabanını `db/` klasöründeki güncel hâline getirmek için aşağıdaki "Veritabanını sıfırla" adımına bak.

## Veritabanını sıfırla (db/ güncellendiğinde)

`db/supply_db.sql` veya `db/data/` değiştiyse (ör. `git pull` sonrası), PostgreSQL verisini silip baştan kur.
**Veritabanındaki tüm değişiklikler gider**; Qdrant verisine dokunulmaz. `kurulum` klasöründe:

```powershell
docker compose down
```

```powershell
docker volume rm docker_supply_postgres_data
```

```powershell
docker compose up -d
```

Python kuruluysa aynı işi önce yedek alarak `db/rebuild_db.py` de yapar (bkz. Notlar).

> **Son değişiklik — herkes bir kez sıfırlamalı:** Süveyş Kanalı lokasyonu ve Kızıldeniz/Süveyş haberi
> (analizleri ve etki bağlantılarıyla) `db/` dosyalarından kaldırıldı, `article_analyses` tablosuna
> `price_change_pct` sütunu eklendi. Daha önce kurulmuş bir veritabanında Süveyş kayıtları kalır;
> `git pull` sonrası yukarıdaki üç komutla sıfırla, sonra "3. Veriyi kontrol et" adımındaki kontrolleri çalıştır.

### Sıfırlamadan güncelleme (yalnızca yeni sütunlar)

Daha önce kurulmuş bir veritabanında veriyi silmeden yalnızca şemaya eklenen sütunları almak için aşağıdaki komutları çalıştır. Birden fazla kez çalıştırmak güvenlidir.

`article_analyses.price_change_pct` (fiyat değişimi %):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "ALTER TABLE article_analyses ADD COLUMN IF NOT EXISTS price_change_pct numeric(6,2)"
```

Bu komut yalnızca sütunu ekler; Süveyş kayıtlarını silmez. Onlar için sıfırlama gerekir.

### Birebir kopya (isteğe bağlı)

`db/` dosyaları kurulumdaki başlangıç verisini içerir. Sonradan taramalarla eklenen haberler, alert'ler
ve elle yapılan değişiklikler dosyalarda yoktur. Veritabanının o anki hâlinin **aynısını** vermek için:

**Veritabanı sahibi** (kendi bilgisayarında, `kurulum` klasöründe) dışa aktarır:

```powershell
docker exec proje_postgres pg_dump -U proje_admin -d supply_db -Fc -f /tmp/supply_db.dump
```

```powershell
docker cp proje_postgres:/tmp/supply_db.dump .
```

Oluşan `supply_db.dump` dosyasını arkadaşına gönder (git'e ekleme).

**Arkadaş** 1. ve 2. adımları yaptıktan sonra dosyayı `kurulum` klasörüne koyup içe aktarır:

```powershell
docker cp supply_db.dump proje_postgres:/tmp/supply_db.dump
```

```powershell
docker exec proje_postgres pg_restore -U proje_admin -d supply_db --clean --if-exists --no-owner /tmp/supply_db.dump
```

Ardından "3. Veriyi kontrol et" adımındaki kontrolleri çalıştır. Kopyada 4. adımda açılan kullanıcılar yer almaz.

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
- `db/rebuild_db.py` veritabanını silip baştan kurar (önce `db/backup/` altına CSV yedek alır, sonra `db/supply_db.sql` ve `db/data/*.sql` yüklenir); yapılan tüm değişiklikler gider. Çalıştırmadan önce ekibe haber verin.
- Yeni veri dosyası eklenecekse `db/data/` içine sıra numarasıyla koyun (ör. `04_....sql`); hem otomatik kurulum hem `rebuild_db.py` onu sırayla yükler.
