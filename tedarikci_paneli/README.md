# Tedarikçi risk paneli (ChainGuard)

Tedarik zinciri risklerini gösteren web sitesi. Veriyi `supply_db` PostgreSQL veritabanından okur (bağlantı henüz yapılmadı).

## Klasör yapısı

| Yol | Ne |
|---|---|
| `web/` | Web sitesi (Nuxt 4). Kurulum ve çalıştırma aşağıda |
| `sirket.md` | Kurgusal alıcı şirket (yıllık üretim adetleri risk hesabında kullanılır) |

## Siteyi çalıştırma

Node.js 22 veya üstü gerekir.

```bash
cd web
# Ayarlar proje kökündeki tek .env dosyasından okunur (kökteki .env.example'dan kopyalayın)
npm ci
npm run dev             # http://localhost:3000
```

- Giriş: `.env`'deki `NUXT_ILK_YONETICI_EPOSTA` / `NUXT_ILK_YONETICI_SIFRE` ile ilk yönetici oluşur.
- Olaylar değerlendirme modelinden gelir; denemek için sunucu açıkken `npm run ornek:gonder` örnek olayları gönderir.
- Uçtan uca testler (Playwright + pytest): `web/` klasöründe `pip install -r e2e/requirements.txt`, `playwright install chromium`, ardından `python -m pytest e2e`. Testler geçici veri klasörü ve rastgele yöneticiyle kendi sunucusunu açar; `.data/veri`'ye dokunmaz. Olay testleri PostgreSQL ister (yalnızca okunur), kapalıysa atlanır.
- Ayrıntılar: `web/RISK_MODELI.md` (risk skoru), `web/MODEL_ENTEGRASYONU.md` (modelin olay ve çıkarım gönderdiği API).
