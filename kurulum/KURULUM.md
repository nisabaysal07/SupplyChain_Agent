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
| `db/supply_db.sql` | Şema: 17 tablo ve indeksler (veri yok) |
| `db/data/01_countries.sql` | 50 ülke |
| `db/data/02_ana_veri.sql` | Tedarikçiler, ürünler (taban gümrük oranlarıyla), lokasyonlar, gümrük oranları, yıllık adetler, sözleşmeler, stok, sevkiyatlar |
| `db/data/03_haberler.sql` | Taramalar ve haberler (mock haberler + agent sonuçları, fiyat değişimi yüzdeleri) |

`cost_impacts` tablosu (Görev 3 maliyet etkisi) boş kurulur; maliyet hesabı çalıştıkça dolar.

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

Şemanın güncel olduğunu kontrol et (17 tablo ve 4 yeni sütun; `17 | 4` çıkmalı):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT (SELECT count(*) FROM pg_tables WHERE schemaname = 'public') AS tablo, (SELECT count(*) FROM information_schema.columns WHERE (table_name, column_name) IN (('article_analyses','price_change_pct'), ('supplier_items','annual_quantity'), ('items','gv_rate_base'), ('items','igv_rate_base'))) AS yeni_sutun"
```

Görev 3 verisinin yüklendiğini kontrol et (`80000 | 6` çıkmalı: toplam yıllık adet, fiyat yüzdesi dolu analiz):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT (SELECT sum(annual_quantity) FROM supplier_items) AS yillik_adet, (SELECT count(*) FROM article_analyses WHERE price_change_pct IS NOT NULL) AS fiyat_yuzdesi"
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

> **Son değişiklik — herkes bir kez sıfırlamalı:** Görev 3 (maliyet etkisi) için şema güncellendi:
> yeni `cost_impacts` tablosu, `supplier_items.annual_quantity` (yıllık adet), `items.gv_rate_base` /
> `igv_rate_base` (taban gümrük oranları) ve fiyat haberlerinde dolu `price_change_pct` değerleri.
> Daha önce kurulmuş bir veritabanı bunları kendiliğinden almaz; `git pull` sonrası yukarıdaki üç komutla
> sıfırla, sonra "3. Veriyi kontrol et" adımındaki kontrolleri çalıştır.

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

## Otomatik tarama (Görev Zamanlayıcı)

`main.py` tüm zinciri çalıştırır: haber taraması → ajan analizi → maliyet etkisi ve alarmlar. Otomatik çalışması için PowerShell'de, proje kökünde:

```powershell
.\kurulum\zamanlayici_kur.ps1
```

- Tarama sıklığı panelin **Ayarlar → Haber tarama sıklığı** alanından seçilir (1, 3, 6, 12 saat veya günde bir; varsayılan 3 saat) ve `app_settings` tablosuna yazılır. Görev saatte bir uyanır; `main.py --schedule` son başarılı taramadan seçilen süre geçmediyse taramadan çıkar (`logs\tarama.log`'a "Tarama atlandı" yazar). Görevi 3 saatlik eski sürümle kurduysanız betiği bir kez yeniden çalıştırın.
- Gerekenler: `.venv` kurulu, kökteki `.env` içinde `TAVILY_API_KEY`, `NEBIUS_API_KEY` ve `POSTGRES_*` dolu, Docker Desktop oturum açılınca başlıyor (Ayarlar → General → Start Docker Desktop when you sign in).
- Görev oturum açıkken (ekran kilitliyken de) pencere açmadan çalışır, böylece `.env`'deki `windows://` masaüstü bildirimleri görünür. Oturum kapalıyken de çalışması için yönetici PowerShell'de `-OturumKapaliyken` ile kurun; bu modda masaüstü bildirimleri görünmez, diğer kanallar (Slack vb.) gelir.
- Uzun süren tarama bitmeden yenisi başlamaz, kapalıyken kaçırılan çalışma bilgisayar açılınca yapılır.
- Çıktılar `logs\tarama.log` dosyasına eklenir; her tarama `scan_logs` tablosuna da yazılır.
- Hemen taramak için: `.venv\Scripts\python main.py` (aralığa bakmaz; `Start-ScheduledTask -TaskName 'SupplyChain Tarama'` ise aralık dolmadıysa atlar) · Kaldır: `.\kurulum\zamanlayici_kur.ps1 -Kaldir`
- `Scheduler.py` aynı işi terminal açık kaldığı sürece yapar (geliştirme için); o da paneldeki aralığı kullanır.

## Veritabanını güncelleme (yeniden kurmadan)

Bu sürümle `locations` tablosuna harita konumu (`latitude`, `longitude`, `city`), veritabanına da `app_settings` tablosu eklendi. Mevcut bir `supply_db`'de koordinatları eklemek için bir kez:

```powershell
cd db; ..\.venv\Scripts\python location_download.py; cd ..
```

`app_settings` tablosunu panel, Ayarlar'da tarama sıklığı ilk kez kaydedilince kendisi oluşturur. `alerts.panel_synced_at` da ilk taramada kendiliğinden eklenir.

## Notlar

- İkiniz aynı ağda olmalısınız. Misafir Wi-Fi ağları cihazların birbirini görmesini çoğu zaman engeller.
- IP adresi modeme yeniden bağlanınca değişebilir; bağlantı koparsa `ipconfig` ile tekrar bak.
- Veritabanı yalnızca bu bilgisayar ve Docker Desktop açıkken erişilebilir.
- `db/rebuild_db.py` veritabanını silip baştan kurar (önce `db/backup/` altına CSV yedek alır, sonra `db/supply_db.sql` ve `db/data/*.sql` yüklenir); yapılan tüm değişiklikler gider. Çalıştırmadan önce ekibe haber verin.
- Yeni veri dosyası eklenecekse `db/data/` içine sıra numarasıyla koyun (ör. `04_....sql`); hem otomatik kurulum hem `rebuild_db.py` onu sırayla yükler.
