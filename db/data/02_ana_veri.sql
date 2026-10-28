-- =====================================================================
-- Ana veri (KurguTek veri seti, kaynak: Tablo_Rehberi.docx)
-- rate_sources, suppliers, items, locations, supplier_items, tariffs, contracts, inventory, shipments
-- ID'ler otomatik atanır; bağlantılar kod/ad üzerinden kurulur.
--
-- Önce db/supply_db.sql (şema) ve sıradaki önceki dosyalar çalıştırılmış olmalı.
--
-- Çalıştırma: python db/rebuild_db.py  (şemayı kurar, sonra db/data/ dosyalarını sırayla yükler)
-- ya da elle:
--   docker cp db/data/02_ana_veri.sql proje_postgres:/tmp/x.sql
--   docker exec proje_postgres psql -U proje_admin -d supply_db -q -v ON_ERROR_STOP=1 -f /tmp/x.sql
-- =====================================================================

BEGIN;

-- =====================================================================
-- ADIM 1a: suppliers  (kaynak: firmalar)
-- country_id = firmanın merkez ülkesi
-- =====================================================================
INSERT INTO suppliers (name, name_original, country_id)
SELECT v.name, v.official, c.id
FROM (VALUES
  ('Intel',         'Intel Corporation',                      'USA'),
  ('Gigabyte',      'GIGA-BYTE Technology Co., Ltd.',         'TWN'),
  ('Kingston',      'Kingston Technology Company, Inc.',      'USA'),
  ('Samsung',       'Samsung Electronics Co., Ltd.',          'KOR'),
  ('ASUS',          'ASUSTeK Computer Inc.',                  'TWN'),
  ('FSP',           'FSP Technology Inc.',                    'TWN'),
  ('Cooler Master', 'Cooler Master Technology Inc.',          'TWN'),
  ('Noctua',        'Rascom Computerdistribution Ges.m.b.H.', 'AUT')
) AS v(name, official, iso)
JOIN countries c ON c.iso_code = v.iso;

-- =====================================================================
-- ADIM 1b: items  (kaynak: parcalar)
-- Oranlar yüzdeye çevrildi: 0,2 → 20 ; 0,01 → 1
-- =====================================================================
INSERT INTO rate_sources (id, name, url) VALUES
  (1, 'TARA (Ticaret Bakanlığı)', 'https://ticaret.gov.tr');
SELECT setval(pg_get_serial_sequence('rate_sources', 'id'), (SELECT MAX(id) FROM rate_sources));

INSERT INTO items (name, hs6, gtip, unit, kdv_rate, otv_rate, kultur_fonu_rate, source_id)
SELECT v.*, (SELECT id FROM rate_sources WHERE name = 'TARA (Ticaret Bakanlığı)')
FROM (VALUES
  ('İşlemci',     '854231', '854231900000', 'adet', 20, 0, 0),
  ('Anakart',     '847330', '847330200000', 'adet', 20, 0, 0),
  ('Bellek',      '847330', '847330200000', 'adet', 20, 0, 0),
  ('SSD',         '847170', '847170989000', 'adet', 20, 0, 1),
  ('Ekran kartı', '847330', '847330200000', 'adet', 20, 0, 0),
  ('Güç kaynağı', '850440', '850440839019', 'adet', 20, 0, 0),
  ('Kasa',        '847330', '847330800000', 'adet', 20, 0, 0),
  ('Soğutucu',    '841459', '841459150000', 'adet', 20, 0, 0),
  ('Monitör',     '852852', '852852100000', 'adet', 20, 0, 0)
) AS v(name, hs6, gtip, unit, kdv_rate, otv_rate, kultur_fonu_rate);

-- =====================================================================
-- ADIM 1c: locations  (kaynak: rotalar tablosundaki çıkış/varış noktaları)
-- Sıra yaml/location.yaml id'leriyle aynıdır
-- =====================================================================
INSERT INTO locations (id, code, name, location_type, country_id)
SELECT v.id, v.code, v.name, v.location_type, c.id
FROM (VALUES
  ( 1, 'SGN',   'Tan Son Nhat Uluslararası Havalimanı', 'airport',    'VNM'),
  ( 2, 'PEN',   'Penang Uluslararası Havalimanı',       'airport',    'MYS'),  -- rotada yok; mock haber verisi kullanıyor
  ( 3, 'ICN',   'Incheon Uluslararası Havalimanı',      'airport',    'KOR'),
  ( 4, 'TWKHH', 'Kaohsiung Limanı',                     'port',       'TWN'),
  ( 5, 'TPE',   'Taoyuan Uluslararası Havalimanı',      'airport',    'TWN'),
  ( 6, 'CNYTN', 'Yantian Limanı (Shenzhen)',            'port',       'CHN'),
  ( 7, 'CNSHK', 'Shekou Limanı (Shenzhen)',             'port',       'CHN'),
  ( 8, 'CNNBG', 'Ningbo-Zhoushan Limanı',               'port',       'CHN'),
  ( 9, 'VNTOT', 'Cai Mep Limanı',                       'port',       'VNM'),
  (10, 'TRMER', 'Mersin Limanı',                        'port',       'TUR'),
  (11, 'IST',   'İstanbul Havalimanı',                  'airport',    'TUR'),
  (12, NULL,    'Süveyş Kanalı',                        'chokepoint', NULL)
) AS v(id, code, name, location_type, iso)
LEFT JOIN countries c ON c.iso_code = v.iso;
SELECT setval(pg_get_serial_sequence('locations', 'id'), (SELECT MAX(id) FROM locations));

-- =====================================================================
-- ADIM 2a: supplier_items  (kaynak: tedarikciler)
-- Her satır = bir tedarikçi satırı (Ted. ID 1-9)
-- =====================================================================
INSERT INTO supplier_items (supplier_id, item_id, item_model, assembly_country_id)
SELECT s.id, i.id, v.model, a.id
FROM (VALUES
  ('Intel',         'İşlemci',     'Intel Core Ultra 5 225 (BX80768225)',                           'VNM'),
  ('Gigabyte',      'Anakart',     'Gigabyte B860 Gaming X WiFi6E (ATX)',                           'CHN'),
  ('Kingston',      'Bellek',      'Kingston FURY Beast 32 GB (2x16) DDR5-6000 (KF560C30BBEK2-32)', 'TWN'),
  ('Samsung',       'SSD',         'Samsung 990 EVO Plus 1 TB (MZ-V9S1T0BW)',                       'KOR'),
  ('ASUS',          'Ekran kartı', 'ASUS Dual GeForce RTX 5060 OC 8 GB (DUAL-RTX5060-O8G)',         'CHN'),
  ('FSP',           'Güç kaynağı', 'FSP VITA GM 650 W (ATX 3.1, 80+ Gold)',                         'CHN'),
  ('Cooler Master', 'Kasa',        'Cooler Master MasterBox TD500 Mesh V2',                         'CHN'),
  ('Noctua',        'Soğutucu',    'Noctua NH-U12S redux',                                          'TWN'),
  ('Samsung',       'Monitör',     'Samsung Odyssey G3 24 inç (LS24DG302ENXZA)',                    'VNM')
) AS v(supplier, item, model, assembly)
JOIN suppliers s ON s.name = v.supplier
JOIN items i     ON i.name = v.item
JOIN countries a ON a.iso_code = v.assembly;

-- =====================================================================
-- ADIM 2b: tariffs  (kaynak: parcalar oranları × ulkeler çarpanları)
-- gv_rate  = parça GV  × ülke GV çarpanı
-- igv_rate = parça İGV × ülke İGV çarpanı (anlaşmalı ülkede 0)
-- Her tedarikçinin parça × menşe ülkesi = 9 satır (sıra yaml/tariffs.yaml id'leriyle aynı)
-- =====================================================================
INSERT INTO tariffs (id, item_id, country_id, gv_rate, igv_rate, valid_from, source_id)
SELECT r.id, i.id, c.id, r.gv * m.gv_mult, r.igv * m.igv_mult, DATE '2026-01-01', rs.id
FROM (VALUES
  -- id, parça,     menşe, GV,  İGV  (tercihsiz oranlar)
  (1, 'İşlemci',     'VNM', 0.0,  0.0),
  (2, 'Anakart',     'CHN', 0.0,  0.0),
  (3, 'Bellek',      'TWN', 0.0,  0.0),
  (4, 'SSD',         'KOR', 0.0,  0.0),
  (5, 'Ekran kartı', 'CHN', 0.0,  0.0),
  (6, 'Güç kaynağı', 'CHN', 3.3, 11.0),
  (7, 'Kasa',        'CHN', 0.0,  0.0),
  (8, 'Soğutucu',    'TWN', 2.3,  0.0),
  (9, 'Monitör',     'VNM', 0.0,  0.0)
) AS r(id, item, iso, gv, igv)
JOIN (VALUES
  ('KOR', 0.0, 0.0),
  ('TWN', 1.0, 1.0),
  ('CHN', 1.0, 1.0),
  ('VNM', 1.0, 1.0)
) AS m(iso, gv_mult, igv_mult) ON m.iso = r.iso
JOIN items i     ON i.name = r.item
JOIN countries c ON c.iso_code = r.iso
JOIN rate_sources rs ON rs.name = 'TARA (Ticaret Bakanlığı)';
SELECT setval(pg_get_serial_sequence('tariffs', 'id'), (SELECT MAX(id) FROM tariffs));
-- =====================================================================
-- ADIM 3a: contracts  (kaynak: tedarikciler — fiyat ve sözleşme tarihleri)
-- unit_price = ABD perakende fiyatı (USD)
-- =====================================================================
INSERT INTO contracts (supplier_item_id, start_date, end_date, currency, unit_price)
SELECT si.id, v.c_start, v.c_end, 'USD', v.price
FROM (VALUES
  ('Intel Core Ultra 5 225 (BX80768225)',                           159.99, DATE '2026-01-01', DATE '2026-12-31'),
  ('Gigabyte B860 Gaming X WiFi6E (ATX)',                           159.99, DATE '2026-01-01', DATE '2026-12-31'),
  ('Kingston FURY Beast 32 GB (2x16) DDR5-6000 (KF560C30BBEK2-32)', 635.00, DATE '2026-10-01', DATE '2026-12-31'),
  ('Samsung 990 EVO Plus 1 TB (MZ-V9S1T0BW)',                       208.15, DATE '2026-10-01', DATE '2026-12-31'),
  ('ASUS Dual GeForce RTX 5060 OC 8 GB (DUAL-RTX5060-O8G)',         469.99, DATE '2026-10-01', DATE '2026-12-31'),
  ('FSP VITA GM 650 W (ATX 3.1, 80+ Gold)',                          99.00, DATE '2026-01-01', DATE '2026-12-31'),
  ('Cooler Master MasterBox TD500 Mesh V2',                         119.99, DATE '2026-01-01', DATE '2026-12-31'),
  ('Noctua NH-U12S redux',                                           59.95, DATE '2026-01-01', DATE '2026-12-31'),
  ('Samsung Odyssey G3 24 inç (LS24DG302ENXZA)',                    179.59, DATE '2026-10-01', DATE '2026-12-31')
) AS v(model, price, c_start, c_end)
JOIN supplier_items si ON si.item_model = v.model;

-- =====================================================================
-- ADIM 3b: inventory  (kaynak: parcalar — stok sütunları)
-- =====================================================================
INSERT INTO inventory (supplier_item_id, on_hand, reserved, reorder_point)
SELECT si.id, v.on_hand, v.reserved, v.reorder
FROM (VALUES
  ('İşlemci',     1014, 192,  438),
  ('Anakart',     1699, 192, 1096),
  ('Bellek',       466, 192,  438),
  ('SSD',          877, 192,  438),
  ('Ekran kartı',  370,  96,  521),
  ('Güç kaynağı', 1151, 192, 1041),
  ('Kasa',        1562, 192, 1068),
  ('Soğutucu',    1014, 192, 1041),
  ('Monitör',      712,  96,  479)
) AS v(item, on_hand, reserved, reorder)
JOIN items i           ON i.name = v.item
JOIN supplier_items si ON si.item_id = i.id;

-- =====================================================================
-- ADIM 4: shipments  (kaynak: rotalar + tedarikciler.mense_ulke_id)
-- =====================================================================
INSERT INTO shipments (contract_id, transport_mode, origin_country_id,
                       exit_location_id, destination_location_id,
                       expected_transit_days)
SELECT ct.id, v.mode, o.id, ex.id, ds.id, v.days
FROM (VALUES
  ('Intel Core Ultra 5 225 (BX80768225)',                           'air', 'VNM', 'SGN',   'IST', 1),
  ('Gigabyte B860 Gaming X WiFi6E (ATX)',                           'sea', 'CHN', 'CNNBG', 'TRMER', 25),
  ('Kingston FURY Beast 32 GB (2x16) DDR5-6000 (KF560C30BBEK2-32)', 'air', 'TWN', 'TPE',   'IST', 1),
  ('Samsung 990 EVO Plus 1 TB (MZ-V9S1T0BW)',                       'air', 'KOR', 'ICN',   'IST', 1),
  ('ASUS Dual GeForce RTX 5060 OC 8 GB (DUAL-RTX5060-O8G)',         'sea', 'CHN', 'CNSHK', 'TRMER', 23),
  ('FSP VITA GM 650 W (ATX 3.1, 80+ Gold)',                         'sea', 'CHN', 'CNSHK', 'TRMER', 23),
  ('Cooler Master MasterBox TD500 Mesh V2',                         'sea', 'CHN', 'CNYTN', 'TRMER', 24),
  ('Noctua NH-U12S redux',                                          'sea', 'TWN', 'TWKHH', 'TRMER', 23),
  ('Samsung Odyssey G3 24 inç (LS24DG302ENXZA)',                    'sea', 'VNM', 'VNTOT', 'TRMER', 20)
) AS v(model, mode, origin, exit_code, dest_code, days)
JOIN supplier_items si ON si.item_model = v.model
JOIN contracts ct      ON ct.supplier_item_id = si.id
JOIN countries o       ON o.iso_code = v.origin
JOIN locations ex      ON ex.code = v.exit_code
JOIN locations ds      ON ds.code = v.dest_code;

COMMIT;
