# PostgreSQL bağlantısı

Uygulama tedarikçi verisini (ülkeler, firmalar, parçalar, tedarikçiler, rotalar) **PostgreSQL**'den okur. `NUXT_DATABASE_URL` tanımlı değilse aynı veriyi proje klasöründeki CSV dosyalarından okur. Bağlantının durumu **Ayarlar → Sistem → Veri kaynağı** bölümünde görünür.

Kullanıcılar, model raporları ve sistem ayarları şimdilik `web/.data/` klasöründe tutulur; bunlar veritabanına taşınmadı.

## 1. Tabloları oluştur

Tablo ve sütun adları CSV'lerle birebir aynıdır (bkz. `VERI_SOZLUGU.md`). Şema dosyası: [`sema.sql`](sema.sql). Tablolar hazırsa bu adımı atlayın.

Tabloları oluşturup CSV'leri tek seferde yüklemek için (`web/` klasöründe):

```bash
npm run db:yukle
```

Bu komut:
- tablolar yoksa oluşturur,
- tabloları boşaltıp CSV'lerdeki veriyle yeniden doldurur,
- hepsini tek işlemde yapar: bir satır bile hatalıysa hiçbir şey değişmez.

Bağlantı adresi için `VERITABANI_YUKLEME_URL` kullanılır (yazma yetkili kullanıcı); bu değişken yoksa `NUXT_DATABASE_URL` kullanılır. CSV'ler `kaynak_veri.py → build_dataset.py` ile güncellendikten sonra aynı komutla tekrar yüklenir.

## 2. Uygulamayı bağla

`web/.env` dosyasına ekleyin, sonra sunucuyu yeniden başlatın:

```
NUXT_DATABASE_URL=postgres://chainguard_okuma:SIFRE@sunucu:5432/veritabani?sslmode=require
```

- Sunucu başka bir makinedeyse `sslmode=require` kullanın; aynı bilgisayardaysa (`localhost`) `sslmode=disable` olabilir.
- Tablolar `public` dışında bir şemadaysa adrese `&options=-c%20search_path%3Dsema_adi` ekleyin.
- Bağlantı adresi şifre içerir: yalnızca `.env`'de tutun, git'e veya sohbete yazmayın.

## Önerilen: salt okunur kullanıcı

Uygulama yalnızca `SELECT` yapar. Uygulamaya yazma yetkisi olmayan ayrı bir kullanıcı verin; uygulama ele geçirilse bile veri değiştirilemez:

```sql
CREATE ROLE chainguard_okuma LOGIN PASSWORD 'guclu-bir-sifre';
GRANT CONNECT ON DATABASE veritabani TO chainguard_okuma;
GRANT USAGE ON SCHEMA public TO chainguard_okuma;
GRANT SELECT ON ulkeler, firmalar, parcalar, tedarikciler, rotalar TO chainguard_okuma;
```

`npm run db:yukle` için ise tablo oluşturma ve yazma yetkisi olan kullanıcıyı `VERITABANI_YUKLEME_URL` ile verin.

## Davranış

- Bağlantı havuzu en fazla 5 bağlantı açar; her sorgu en fazla 5 saniye sürebilir.
- Veritabanına ulaşılamazsa sayfalar "Veritabanına ulaşılamadı" (503) gösterir. Hatanın ayrıntısı (sunucu adı, kullanıcı) tarayıcıya gönderilmez, yalnızca sunucu günlüğüne yazılır.
- `DATE` sütunları saat dilimi kayması olmadan `YYYY-AA-GG` olarak okunur.

Testler (`test/veritabani.test.ts`) gerçek bir PostgreSQL'e (PGlite) bağlanır: şemayı kurar, CSV'leri yükler ve veritabanından okunan verinin CSV'lerle birebir aynı olduğunu doğrular.
