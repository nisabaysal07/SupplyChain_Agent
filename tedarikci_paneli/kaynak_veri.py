"""
Tedarikçi veri seti — TEK VERİ KAYNAĞI.

Bütün CSV tabloları bu dosyadan üretilir (build_dataset.py). Bir bilgiyi değiştirmek için
CSV'yi değil bu dosyayı düzenleyip build_dataset.py'yi yeniden çalıştırın.

Alıcı şirket (KurguTek Bilgisayar A.Ş.) KURGUSALDIR. Tedarikçi firmalar ve ürünler GERÇEKTİR;
stok sayıları ve sözleşme tarihleri şirket kararı olarak tahmini değerlerdir.
"""

# ---------------------------------------------------------------------------
# ÜLKELER — anlasma_durumu: Türkiye ile serbest ticaret anlaşması var (1) / yok (0)
#           gv_carpani, igv_carpani: parçanın tercihsiz vergi oranının çarpanı. Anlaşmalı ülkede sanayi ürünlerinde
#           gümrük vergisi ve İGV alınmaz (Kore STA: 2020'ye kadar sıfırlandı; menşe ispatıyla).
# ---------------------------------------------------------------------------
ULKELER = [
    # (ulke_id, ulke_adi, anlasma_durumu, gv_carpani, igv_carpani)
    (1, 'Güney Kore', 1, 0.0, 0.0),
    (2, 'Tayvan', 0, 1.0, 1.0),
    (3, 'Çin', 0, 1.0, 1.0),
    (4, 'Vietnam', 0, 1.0, 1.0),
]

# ---------------------------------------------------------------------------
# FİRMALAR
# ---------------------------------------------------------------------------
FIRMALAR = [
    # (firma_id, firma_adi, resmi_ad, merkez_ulke)
    (1, 'Intel', 'Intel Corporation', 'Amerika Birleşik Devletleri'),
    (2, 'Gigabyte', 'GIGA-BYTE Technology Co., Ltd.', 'Tayvan'),
    (3, 'Kingston', 'Kingston Technology Company, Inc.', 'Amerika Birleşik Devletleri'),
    (4, 'Samsung', 'Samsung Electronics Co., Ltd.', 'Güney Kore'),
    (5, 'ASUS', 'ASUSTeK Computer Inc.', 'Tayvan'),
    (6, 'FSP', 'FSP Technology Inc.', 'Tayvan'),
    (7, 'Cooler Master', 'Cooler Master Technology Inc.', 'Tayvan'),
    (8, 'Noctua', 'Rascom Computerdistribution Ges.m.b.H.', 'Avusturya'),
]

# ---------------------------------------------------------------------------
# PARÇALAR — GTİP ve vergi oranları (TARA, Ticaret Bakanlığı; tercihsiz menşe) ve stok
#   Stoklar tahminidir ve parçadan parçaya farklıdır: eldeki = (kullanılabilir gün + 7) günlük kullanım,
#   rezerve = 7 günlük kullanım. Kullanılabilir stok: işlemci 30, anakart 55, bellek 10, SSD 25,
#   ekran kartı 20, güç kaynağı 35, kasa 50, soğutucu 30, monitör 45 gün.
#   Yeniden sipariş seviyesi = (yol + gümrük 1 gün + 14 gün güvenlik) günlük kullanım.
#   Günlük kullanım = yıllık ihtiyaç ÷ 365 (yılda 10.000 bilgisayar; ekran kartı ve monitör 5.000).
# ---------------------------------------------------------------------------
ORAN_KAYNAGI = 'TARA (Ticaret Bakanlığı)'
KDV_ORANI = 0.2
PARCALAR = [
    # (parca_id, parca_adi, hs6, gtip12, gv, igv, kultur_fonu, otv, eldeki_stok, rezerve_stok, yeniden_siparis_seviyesi)
    (1, 'İşlemci', '854231', '854231900000', 0.0, 0.0, 0.0, 0.0, 1014, 192, 438),
    (2, 'Anakart', '847330', '847330200000', 0.0, 0.0, 0.0, 0.0, 1699, 192, 1096),
    (3, 'Bellek', '847330', '847330200000', 0.0, 0.0, 0.0, 0.0, 466, 192, 438),
    (4, 'SSD', '847170', '847170989000', 0.0, 0.0, 0.01, 0.0, 877, 192, 438),
    (5, 'Ekran kartı', '847330', '847330200000', 0.0, 0.0, 0.0, 0.0, 370, 96, 521),
    (6, 'Güç kaynağı', '850440', '850440839019', 0.033, 0.11, 0.0, 0.0, 1151, 192, 1041),
    (7, 'Kasa', '847330', '847330800000', 0.0, 0.0, 0.0, 0.0, 1562, 192, 1068),
    (8, 'Soğutucu', '841459', '841459150000', 0.023, 0.0, 0.0, 0.0, 1014, 192, 1041),
    (9, 'Monitör', '852852', '852852100000', 0.0, 0.0, 0.0, 0.0, 712, 96, 479),
]

# ---------------------------------------------------------------------------
# TEDARİKÇİLER — her parça için tek tedarikçi; tüm alım bu tedarikçiden
#   rota = (mod, çıkış noktası, aktarma noktası, varış noktası, yol günü)
#   Liman ve havalimanları resmi tam adlarıyla yazılır. Sözleşme tarihleri şirket kararıdır.
# ---------------------------------------------------------------------------
TEDARIKCILER = [
  dict(tedarikci_id=1, parca_id=1, firma_id=1, mense_ulke_id=4,
       birlestirme='Vietnam',
       fiyat=159.99, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-01-01', '2026-12-31'),
       rota=('hava', 'Tan Son Nhat International Airport', 'Aktarma yok', 'Istanbul Airport', 1)),
  dict(tedarikci_id=2, parca_id=2, firma_id=2, mense_ulke_id=3,
       birlestirme='Çin',
       fiyat=159.99, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-01-01', '2026-12-31'),
       rota=('deniz', 'Port of Ningbo-Zhoushan', 'Aktarma yok', 'Port of Mersin', 25)),
  dict(tedarikci_id=3, parca_id=3, firma_id=3, mense_ulke_id=2,
       birlestirme='Tayvan',
       fiyat=635.0, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-10-01', '2026-12-31'),
       rota=('hava', 'Taiwan Taoyuan International Airport', 'Aktarma yok', 'Istanbul Airport', 1)),
  dict(tedarikci_id=4, parca_id=4, firma_id=4, mense_ulke_id=1,
       birlestirme='Güney Kore',
       fiyat=208.15, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-10-01', '2026-12-31'),
       rota=('hava', 'Incheon International Airport', 'Aktarma yok', 'Istanbul Airport', 1)),
  dict(tedarikci_id=5, parca_id=5, firma_id=5, mense_ulke_id=3,
       birlestirme='Çin',
       fiyat=469.99, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-10-01', '2026-12-31'),
       rota=('deniz', 'Port of Shekou (Shenzhen)', 'Aktarma yok', 'Port of Mersin', 23)),
  dict(tedarikci_id=6, parca_id=6, firma_id=6, mense_ulke_id=3,
       birlestirme='Çin',
       fiyat=99.0, fiyat_tarihi='2024-04-11',
       sozlesme=('2026-01-01', '2026-12-31'),
       rota=('deniz', 'Port of Shekou (Shenzhen)', 'Aktarma yok', 'Port of Mersin', 23)),
  dict(tedarikci_id=7, parca_id=7, firma_id=7, mense_ulke_id=3,
       birlestirme='Çin',
       fiyat=119.99, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-01-01', '2026-12-31'),
       rota=('deniz', 'Port of Yantian (Shenzhen)', 'Aktarma yok', 'Port of Mersin', 24)),
  dict(tedarikci_id=8, parca_id=8, firma_id=8, mense_ulke_id=2,
       birlestirme='Tayvan',
       fiyat=59.95, fiyat_tarihi='2026-10-21',
       sozlesme=('2026-01-01', '2026-12-31'),
       rota=('deniz', 'Port of Kaohsiung', 'Aktarma yok', 'Port of Mersin', 23)),
  dict(tedarikci_id=9, parca_id=9, firma_id=4, mense_ulke_id=4,
       birlestirme='Vietnam',
       fiyat=179.59, fiyat_tarihi='2026-10-13',
       sozlesme=('2026-10-01', '2026-12-31'),
       rota=('deniz', 'Cai Mep Port', 'Aktarma yok', 'Port of Mersin', 20)),
]
