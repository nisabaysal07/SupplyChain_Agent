# Tedarikçi risk modeli

Her tedarikçi için **0–100** arası, kural tabanlı ve açıklanabilir bir risk skoru hesaplanır. Skor beş bileşenin toplamıdır; her bileşenin puanı ve gerekçesi arayüzde ayrı ayrı gösterilir. Kod: `server/utils/risk.ts`, testler: `test/risk.test.ts`.

| Seviye | Skor |
|---|---|
| Düşük | 0–34 |
| Orta | 35–59 |
| Yüksek | 60–100 |

## Bileşenler

| Bileşen | En fazla | Kural |
|---|---|---|
| Stok | 30 | `oran = kullanılabilir stok ÷ yeniden sipariş seviyesi`. Oran ≥ 1,5 → 0; oran ≤ 0,5 → 30; arası doğrusal: `30 × (1,5 − oran)` |
| Rota | 20 | `20 × min(1, yol günü ÷ 30)`. Uzun yol, aksaklıkta toparlanmayı geciktirir |
| Ticaret | 15 | Türkiye ile serbest ticaret anlaşması yoksa 10; menşe çarpanı uygulanmış gümrük vergisi + İGV > 0 ise +5 |
| Sözleşme | 10 | Bitişe ≤ 30 gün (veya bitmiş) → 10; ≤ 90 gün → 5; fazlası → 0 |
| Olaylar | 25 | Tedarikçiyi etkileyen aktif olaylardan en ağırının puanı (düşük 5, orta 15, yüksek 25) + diğer her olay için 5; en fazla 25 |

*Kullanılabilir stok* = eldeki − rezerve. Bütün tedarikçiler tek kaynaklı olduğu için "tek tedarikçi" ayrıca puanlanmaz; ikinci tedarikçi eklendiğinde ayrı bir bileşen olarak eklenmelidir.

## Olay eşleşmesi

Bir olayın kapsamında dört ölçüt olabilir: **ülkeler** (menşe ülke), **noktalar** (rotadaki çıkış, aktarma veya varış noktası), **hs6** ve **firmalar**. Bir olayın tedarikçiyi etkilemesi için **verilen ölçütlerin hepsi** sağlanmalıdır (bir ölçüt içindeki listeden biri yeterlidir). Örneğin `{ ulkeler: [Çin], hs6: [850440] }` yalnızca Çin menşeli güç kaynaklarını etkiler. Ölçütsüz olay kimseyi etkilemez.

Olay, `tarih ≤ bugün` ve (`bitisTarihi` yok veya `≥ bugün`) ise aktiftir. "Bugün" Europe/Istanbul saat dilimine göre alınır.

Adlar CSV'lerdekiyle birebir aynı yazılmalıdır (ör. `Port of Mersin`, `Güney Kore`).

## Olay etkisi

Her olay–tedarikçi eşleşmesi için:

- **Maliyet etkisi** = yıllık alım tutarı × `ekMaliyetOrani` (ek vergi veya fiyat artışı)
- **Gecikme**: haberden gecikmenin süresi çıkarılamaz; olay yalnızca gecikme beklenip beklenmediğini taşır (`gecikmeVar`). Gecikme yoksa arayüzde gecikme bölümü hiç gösterilmez.
- **Gecikmede stok yetmeyebilir** uyarısı: gecikme bekleniyor **ve** tedarikçinin stoğu zaten yeniden sipariş seviyesinin altında

## Portföy skoru

Kontrol panelindeki portföy skoru, tedarikçi skorlarının **yıllık alım tutarıyla ağırlıklı** ortalamasıdır: büyük alım yapılan tedarikçinin riski daha çok sayılır.

## Yıllık adet

CSV'de yıllık adet sütunu yoktur. `sirket.md`'ye göre yılda 10.000 bilgisayar üretilir; ekran kartı ve monitör modellerin yarısında olduğu için 5.000 adettir (`server/utils/veri.ts`).

## Olayların kaynağı

Olaylar değerlendirme modelinden gelir (`POST /api/model/olaylar`, bkz. MODEL_ENTEGRASYONU.md) ve `.data/veri/olay/` altında saklanır. Risk skoru her istekte o anki olaylarla yeniden hesaplanır. Denemek için `npm run ornek:gonder` `ornek/olaylar/` altındaki örnek senaryoları gönderir; bunlar gerçek haber değildir (`ornek: true`).
