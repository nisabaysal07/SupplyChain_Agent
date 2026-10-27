# Tedarikçi veri seti — veri sözlüğü

Tablolar **üretilir**; elle düzenlemeyin. Tek kaynak `kaynak_veri.py`, üretici `build_dataset.py`. Alıcı şirket KurguTek kurgusaldır (bkz. `sirket.md`); tedarikçiler, ürünler, fiyatlar, menşeler ve rotalar gerçektir. Stok sayıları ve sözleşme tarihleri tahmini şirket kararlarıdır. Hiçbir hücre boş değildir.

**Dosya biçimi:** CSV'ler `;` (noktalı virgül) ayırıcılı ve UTF-8 (BOM) yazılır; Türkçe Excel'de çift tıklanınca sütunlara ayrılmış açılır. Ondalık ayırıcı noktadır (`159.99`). Veritabanına aktarırken ayırıcı olarak `;` seçilmelidir (ör. pandas: `read_csv(dosya, sep=";")`).

## Tablolar ve bağlantılar

| Tablo | Satır | Bir satır | Birincil anahtar | Bağlantılar |
|---|---|---|---|---|
| `tedarikciler.csv` | 9 | Bir parçanın tedarikçisi | `tedarikci_id` | `parca_id` → parcalar · `firma_id` → firmalar · `mense_ulke_id` → ulkeler |
| `rotalar.csv` | 9 | Bir tedarikçinin rotası | `tedarikci_id` | `tedarikci_id` → tedarikciler |
| `parcalar.csv` | 9 | Bir parça türü | `parca_id` | — |
| `ulkeler.csv` | 4 | Bir menşe ülke | `ulke_id` | — |
| `firmalar.csv` | 8 | Bir üretici firma | `firma_id` | — |

## tedarikciler.csv

| Sütun | Açıklama |
|---|---|
| `tedarikci_id` | Tedarikçi kimliği (sayı) |
| `parca_id`, `firma_id`, `mense_ulke_id` | Bağlantılar → parcalar, firmalar, ulkeler |
| `birlestirme_ulke` | Ürünün birleştirildiği ülke |
| `perakende_usd`, `fiyat_tarihi` | ABD perakende fiyatı ve tarihi |
| `sozlesme_baslangic`, `sozlesme_bitis` | Fiyat sözleşmesinin başlangıç ve bitiş tarihi |

## rotalar.csv

| Sütun | Açıklama |
|---|---|
| `tedarikci_id` | Bağlantı → tedarikciler |
| `tasima_modu` | deniz veya hava |
| `cikis_noktasi` | Çıkış limanı veya havalimanının resmi adı (ör. Port of Shekou (Shenzhen), Taiwan Taoyuan International Airport) |
| `aktarma_noktasi` | Aktarma yapılan havalimanı; yoksa `Aktarma yok` |
| `varis_noktasi` | Port of Mersin veya Istanbul Airport |
| `transit_gun` | Yol süresi (gün) |

## parcalar.csv

| Sütun | Açıklama |
|---|---|
| `parca_id`, `parca_adi` | Parça kimliği (sayı) ve adı |
| `hs6`, `gtip12` | 6 haneli uluslararası ve 12 haneli Türkiye GTİP kodu |
| `tarife_gv_tercihsiz`, `tarife_igv_tercihsiz` | Anlaşmasız ülke için gümrük vergisi ve ilave gümrük vergisi (oran) |
| `kultur_fonu_orani`, `otv_orani`, `kdv_orani` | Kültür Fonu, ÖTV ve KDV oranları |
| `oran_kaynagi` | Oranların kaynağı |
| `eldeki_stok` | Depodaki adet (tahmini, parçaya göre farklı: rezerve dışında 10–55 günlük kullanım) |
| `rezerve_stok` | Siparişlere ayrılmış adet (tahmini: 7 günlük kullanım) |
| `yeniden_siparis_seviyesi` | Stok bu sayıya düşünce yeni sipariş verilir (tahmini: yol + gümrük + 14 günlük kullanım) |

## ulkeler.csv

| Sütun | Açıklama |
|---|---|
| `ulke_id`, `ulke_adi` | Ülke kimliği (sayı) ve adı |
| `anlasma_durumu` | Türkiye ile serbest ticaret anlaşması: 1 var, 0 yok |
| `gv_carpani`, `igv_carpani` | Parçanın gümrük vergisi ve İGV oranının bu ülke için çarpanı (anlaşmalı ülkede sanayi ürünlerinde gümrük vergisi ve İGV alınmaz: iki çarpan da 0) |

## firmalar.csv

| Sütun | Açıklama |
|---|---|
| `firma_id`, `firma_adi` | Firma kimliği (sayı) ve kısa adı |
| `resmi_ad` | Resmi ticari adı |
| `merkez_ulke` | Genel merkezin bulunduğu ülke |
