# Değerlendirme modeli entegrasyonu

Model haberleri bulur ve her haberi bir **olay** olarak, o haberden yaptığı **çıkarımla** birlikte ChainGuard'a gönderir. Panelin bütün olay verisi modelden gelir:

- Olay, tedarikçilerin **risk skoruna**, Kontrol Paneli'ndeki **kritik olaylara** ve **haritaya** girer.
- Çıkarım, **Olaylar** sayfasında olayın detayında gösterilir: önce haberin genel bilgileri, ardından modelin çıkarımı.

Kullanıcılar olay veya rapor oluşturmaz.

## Uç noktalar

Bütün istekler gizli erişim anahtarıyla yapılır:

```
Authorization: Bearer <NUXT_MODEL_API_TOKEN>
```

| Uç | Ne yapar |
|---|---|
| `POST /api/model/olaylar` | Bir olayı (haber + isteğe bağlı çıkarım) gönderir |
| `GET /api/model/referans` | Kapsamda kullanılabilecek adları verir: ülkeler, limanlar/havalimanları, HS6 kodları, firmalar, tedarikçi kimlikleri |

- Erişim anahtarı sunucudaki proje kökü `.env` dosyasında `NUXT_MODEL_API_TOKEN` olarak durur (en az 32 karakter). Model geliştiricisiyle güvenli bir yoldan paylaşın; koda, git'e veya sohbete yazmayın. Anahtar boşsa uçlar kapalıdır (503).
- Aynı `id` ile tekrar gönderilen olay öncekinin **yerine geçer**. Model önce haberi, çıkarımı hazır olunca da aynı olayı çıkarımıyla yeniden gönderebilir.
- Gövde en fazla 1 MB olabilir.

## Yanıtlar (`POST /api/model/olaylar`)

| Kod | Anlamı |
|---|---|
| 201 | Olay oluşturuldu: `{ "id": "...", "durum": "olusturuldu", "bildirilenKullanici": 1, "uyarilar": [] }` |
| 200 | Aynı `id`'li olay güncellendi: `{ "id": "...", "durum": "guncellendi", "bildirilenKullanici": 0, "uyarilar": [] }` |
| 400 | Biçim geçersiz. `data` alanında hangi alanın neden reddedildiği yazar: `[{ "alan": "kapsam.hs6.0", "hata": "..." }]` |
| 401 | Erişim anahtarı yok veya yanlış |
| 413 | Gövde 1 MB'tan büyük |
| 429 | Çok sık istek (5 dakikada 150) |
| 503 | Sunucuda erişim anahtarı tanımlı değil |

**`bildirilenKullanici`:** Bu gönderim için kaç kullanıcıya uygulama içi bildirim düştüğü. Yeni bir haber veya yeni bir çıkarım (`cikarim.olusturma` değişince) bildirim üretir; aynı haberin değişmeden ya da yalnızca metni düzeltilerek yeniden gönderilmesi üretmez. Bitmiş olaylar bildirilmez. Kullanıcılar hangi seviyeleri alacaklarını Ayarlar'dan seçer; seviye çıkarım varsa `cikarim.genelDegerlendirme.seviye`, yoksa `siddet`'tir.

**`uyarilar`:** Kapsamda panelin tanımadığı bir ad varsa (ör. `"China"` yerine `"Çin"` olmalıydı) olay yine kaydedilir, ama o ad hiçbir tedarikçiyle eşleşmez ve uyarı döner. Doğru adlar `GET /api/model/referans` yanıtındadır.

## Olay biçimi

| Alan | Tür | Zorunlu | Açıklama |
|---|---|---|---|
| `id` | metin | evet | Modelin verdiği tekil kimlik. Yalnızca harf, rakam, `-`, `_`; en fazla 100 karakter |
| `baslik` | metin | evet | Haberin başlığı, en fazla 200 karakter |
| `ozet` | metin | evet | Haberin kısa özeti, en fazla 2000 karakter |
| `tur` | `vergi` \| `grev` \| `liman` \| `dogal_afet` \| `jeopolitik` \| `fiyat` | evet | Olayın türü |
| `siddet` | `dusuk` \| `orta` \| `yuksek` | evet | Risk skoruna girer: düşük 5, orta 15, yüksek 25 puan |
| `tarih` | `YYYY-AA-GG` | evet | Olayın başladığı gün |
| `bitisTarihi` | `YYYY-AA-GG` veya `null` | hayır | Bitiş günü; yoksa olay süresiz aktiftir. Bitiş geçince olay risk skoruna girmez |
| `kaynak` | `{ ad, url? }` | evet | Haberin kaynağı; `url` yalnızca `https://` |
| `kapsam` | `{ ulkeler?, noktalar?, hs6?, firmalar? }` | evet | Olayın hangi tedarikçileri etkilediği (aşağıya bakın). En az bir ölçüt olmalı |
| `ekMaliyetOrani` | sayı (0–5) | hayır | Ek vergi veya fiyat artışı oranı; `0.10` = %10. Etkilenen tedarikçinin yıllık alımıyla çarpılır |
| `gecikmeVar` | `true` / `false` | hayır | Sevkiyatlarda gecikme bekleniyor mu (varsayılan `false`). Süre (gün) beklenmez |
| `ornek` | `true` / `false` | hayır | Deneme verisi mi; `true` ise arayüzde "Örnek olay" yazar (varsayılan `false`) |
| `cikarim` | nesne | hayır | Modelin bu haberden yaptığı çıkarım (aşağıya bakın) |

### Kapsam

Bir olayın tedarikçiyi etkilemesi için kapsamda **verilen ölçütlerin hepsi** sağlanmalıdır; bir ölçüt içindeki listeden biri yeterlidir. Örnek: `{ "ulkeler": ["Çin"], "hs6": ["850440"] }` yalnızca Çin menşeli güç kaynaklarını etkiler.

| Ölçüt | Eşleştiği bilgi |
|---|---|
| `ulkeler` | Tedarikçinin menşe ülkesi (`Çin`, `Tayvan`, `Güney Kore`, `Vietnam`) |
| `noktalar` | Rotanın çıkış, aktarma veya varış noktası, resmi adıyla (`Port of Mersin`, `Istanbul Airport`, …) |
| `hs6` | Parçanın 6 haneli HS kodu |
| `firmalar` | Üretici firmanın kısa adı (`ASUS`, `Kingston`, …) |

Adlar paneldekilerle **birebir** aynı yazılmalıdır; güncel liste `GET /api/model/referans` yanıtındadır.

### Çıkarım

| Alan | Tür | Zorunlu | Açıklama |
|---|---|---|---|
| `baslik` | metin | evet | Çıkarımın başlığı, en fazla 200 karakter |
| `olusturma` | ISO 8601 tarih-saat | evet | Saat dilimiyle: `2026-10-24T09:00:00+03:00` |
| `model` | `{ ad, surum }` | evet | Çıkarımı üreten model ve sürümü |
| `ozet` | metin | evet | En fazla 5000 karakter. Düz metin; satır sonları korunur |
| `genelDegerlendirme` | `{ seviye, skor?, guven? }` | evet | `seviye`: `dusuk`/`orta`/`yuksek`; `skor`: 0–100; `guven`: 0–1 |
| `bulgular` | liste (en fazla 50) | hayır | `{ baslik, aciklama, seviye, tedarikciIdleri? }` |
| `oneriler` | liste (en fazla 50) | hayır | `{ metin, oncelik }`; `oncelik`: `dusuk`/`orta`/`yuksek` |
| `kaynaklar` | liste (en fazla 50) | hayır | `{ ad, url }`; `url` yalnızca `https://` |

`tedarikciIdleri`, `GET /api/model/referans` yanıtındaki `tedarikciler[].id` değerleridir. Arayüz bunları tedarikçi adına çevirir.

**Metinler:** HTML veya Markdown işlenmez, her şey düz metin olarak gösterilir. `<`, `>` gibi karakterler güvenle kullanılabilir.

Örnekler: [`ornek/olaylar/`](ornek/olaylar/) (`ornek-2.json` çıkarım içerir). Biçimin kesin tanımı (zod şeması): `shared/utils/modelOlayi.ts`.

## Deneme

Sunucu çalışırken, `web/` klasöründe örnek olayların hepsini modelin yapacağı gibi gönderin:

```bash
npm run ornek:gonder
```

Tek bir olayı curl ile:

```bash
curl -X POST http://localhost:3000/api/model/olaylar \
  -H "Authorization: Bearer $NUXT_MODEL_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @ornek/olaylar/ornek-2.json
```

Python ile:

```python
import json, os, requests

ANAHTAR = os.environ["NUXT_MODEL_API_TOKEN"]
SUNUCU = "http://localhost:3000"
basliklar = {"Authorization": f"Bearer {ANAHTAR}"}

# Kapsamda kullanılabilecek adlar
referans = requests.get(f"{SUNUCU}/api/model/referans", headers=basliklar, timeout=30).json()

with open("ornek/olaylar/ornek-2.json", encoding="utf-8") as f:
    olay = json.load(f)

yanit = requests.post(f"{SUNUCU}/api/model/olaylar", json=olay, headers=basliklar, timeout=30)
print(yanit.status_code, yanit.json())
```

Hatalı veya deneme olaylarını yönetici, Olaylar sayfasında olayın sağ üstündeki çöp kutusu düğmesiyle (çıkarımıyla birlikte) kaldırabilir.
