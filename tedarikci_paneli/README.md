# Tedarikçi risk paneli (ChainGuard)

Tedarik zinciri risklerini gösteren web sitesi ve çalışmasını sağlayan veri seti.

## Klasör yapısı

| Yol | Ne |
|---|---|
| `web/` | Web sitesi (Nuxt 4). Kurulum ve çalıştırma aşağıda |
| `tedarikciler.csv`, `rotalar.csv`, `parcalar.csv`, `ulkeler.csv`, `firmalar.csv` | Sitenin okuduğu veri seti (`;` ayırıcılı, UTF-8). Site bu dosyaları `web/` klasörünün bir üstünde arar |
| `kaynak_veri.py` | Veri setinin tek kaynağı; bir bilgi değişecekse burası düzenlenir |
| `build_dataset.py` | `kaynak_veri.py`'den CSV'leri üretir: `python build_dataset.py` |
| `VERI_SOZLUGU.md` | Tabloların ve sütunların açıklaması |
| `sirket.md` | Kurgusal alıcı şirket (yıllık üretim adetleri risk hesabında kullanılır) |

## Siteyi çalıştırma

Node.js 22 veya üstü gerekir.

```bash
cd web
cp .env.example .env    # değerleri doldurun (ilk yönetici e-postası ve şifresi, model erişim anahtarı)
npm ci
npm run dev             # http://localhost:3000
```

- Giriş: `.env`'deki `NUXT_ILK_YONETICI_EPOSTA` / `NUXT_ILK_YONETICI_SIFRE` ile ilk yönetici oluşur.
- Olaylar değerlendirme modelinden gelir; denemek için sunucu açıkken `npm run ornek:gonder` örnek olayları gönderir.
- Ayrıntılar: `web/RISK_MODELI.md` (risk skoru), `web/MODEL_ENTEGRASYONU.md` (modelin olay ve çıkarım gönderdiği API), `web/db/README.md` (PostgreSQL bağlantısı).
