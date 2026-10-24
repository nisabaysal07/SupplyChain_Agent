-- =====================================================================
-- Haber / risk tarafı → MOCK veri
-- Boş olan tablolar: scan_logs, articles, article_analyses, article_impacts
-- Önce şema, countries_data.sql ve data_inserts.sql çalıştırılmış olmalı.
-- ID'ler otomatik atanır; bağlantılar url / kod / ad üzerinden kurulur.
-- URL'ler example.com altında, haberler kurgusaldır.
-- =====================================================================

BEGIN;

-- =====================================================================
-- ADIM 1: scan_logs
-- =====================================================================
INSERT INTO scan_logs (triggered_by, status, started_at, finished_at, error_message) VALUES
  ('schedule', 'success', TIMESTAMPTZ '2026-10-18 06:00:00+03', TIMESTAMPTZ '2026-10-18 06:04:12+03', NULL),
  ('schedule', 'success', TIMESTAMPTZ '2026-10-19 06:00:00+03', TIMESTAMPTZ '2026-10-19 06:03:47+03', NULL),
  ('schedule', 'failed',  TIMESTAMPTZ '2026-10-20 06:00:00+03', TIMESTAMPTZ '2026-10-20 06:00:31+03', 'Haber kaynağına bağlanılamadı: timeout (30s)'),
  ('manual',   'success', TIMESTAMPTZ '2026-10-20 14:25:00+03', TIMESTAMPTZ '2026-10-20 14:29:05+03', NULL),
  ('schedule', 'success', TIMESTAMPTZ '2026-10-21 06:00:00+03', TIMESTAMPTZ '2026-10-21 06:05:20+03', NULL),
  ('schedule', 'success', TIMESTAMPTZ '2026-10-22 06:00:00+03', TIMESTAMPTZ '2026-10-22 06:04:02+03', NULL),
  ('schedule', 'running', TIMESTAMPTZ '2026-10-23 06:00:00+03', NULL,                               NULL);

-- =====================================================================
-- ADIM 2: articles
-- first_seen_scan_id = last_seen_scan_id = haberi getiren tarama (başlangıç zamanı ile eşlenir)
-- content_hash = sha256(küçük harf + boşlukları tek boşluğa indirgenmiş "title content"), hex
-- =====================================================================
INSERT INTO articles (first_seen_scan_id, last_seen_scan_id, url, content_hash, title, content,
                      language, published_at, effective_date)
SELECT sl.id, sl.id, v.url,
       encode(sha256(convert_to(lower(regexp_replace(trim(v.title || ' ' || coalesce(v.content, '')), '\s+', ' ', 'g')), 'UTF8')), 'hex'),
       v.title, v.content, v.lang, v.published, v.effective
FROM (VALUES
  (TIMESTAMPTZ '2026-10-18 06:00:00+03',
   'https://example.com/haber/2026/10/cin-mensheli-guc-kaynaklarina-ilave-gumruk-vergisi',
   'Çin menşeli güç kaynaklarına ilave gümrük vergisi artırıldı',
   'Resmî Gazete''de yayımlanan karar ile 8504.40 GTİP pozisyonundaki Çin menşeli güç kaynaklarına uygulanan ilave gümrük vergisi %11''den %20''ye çıkarıldı. Karar 1 Kasım 2026 itibarıyla yürürlüğe girecek.',
   'tr', TIMESTAMPTZ '2026-10-17 23:30:00+03', TIMESTAMPTZ '2026-11-01 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-18 06:00:00+03',
   'https://example.com/news/2026/10/red-sea-attacks-suez-diversions',
   'Container lines divert vessels away from Suez Canal after renewed Red Sea attacks',
   'Several major carriers announced that Asia–Europe services will be rerouted via the Cape of Good Hope, adding 10 to 14 days to transit times. Freight rates on the Shanghai–Mediterranean lane rose sharply.',
   'en', TIMESTAMPTZ '2026-10-17 15:10:00+03', TIMESTAMPTZ '2026-10-20 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-18 06:00:00+03',
   'https://example.com/news/2026/10/local-football-results',
   'Weekend football results roundup',
   'A summary of weekend league matches and standings.',
   'en', TIMESTAMPTZ '2026-10-17 21:00:00+03', NULL),
  (TIMESTAMPTZ '2026-10-19 06:00:00+03',
   'https://example.com/news/2026/10/dram-contract-prices-surge-q4',
   'DRAM contract prices expected to jump 15% in Q4 as AI demand tightens supply',
   'Market analysts expect DDR5 contract prices to rise by roughly 15% quarter over quarter, as memory makers shift capacity to HBM for AI accelerators. Module makers including Kingston are expected to pass on the increase.',
   'en', TIMESTAMPTZ '2026-10-18 10:45:00+03', TIMESTAMPTZ '2026-10-01 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-19 06:00:00+03',
   'https://example.com/news/2026/10/kaohsiung-typhoon-port-closure',
   'Typhoon forces temporary closure of Kaohsiung port',
   'Port authorities suspended all berthing operations at Kaohsiung for at least three days as a strong typhoon approaches southern Taiwan. Backlogs are expected to persist into next week.',
   'en', TIMESTAMPTZ '2026-10-18 18:20:00+03', TIMESTAMPTZ '2026-10-19 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-20 14:25:00+03',
   'https://example.com/news/2026/10/nvidia-rtx-5060-supply-shortage',
   'Graphics card shortage: RTX 5060 board partners report constrained GPU allocation',
   'Board partners such as ASUS and Gigabyte report reduced GPU allocations for the RTX 5060 series, with retail prices climbing 8–12% in several markets.',
   'en', TIMESTAMPTZ '2026-10-20 09:00:00+03', TIMESTAMPTZ '2026-10-20 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-20 14:25:00+03',
   'https://example.com/haber/2026/10/kultur-fonu-orani-degisikligi',
   'Bilgisayar depolama ürünlerinde kültür fonu kesintisi oranı yükseltildi',
   'Cumhurbaşkanı kararı ile 8471.70 pozisyonundaki depolama birimlerine uygulanan kültür fonu oranı %1''den %2''ye çıkarıldı.',
   'tr', TIMESTAMPTZ '2026-10-20 11:15:00+03', TIMESTAMPTZ '2026-11-15 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-21 06:00:00+03',
   'https://example.com/news/2026/10/malaysia-penang-airport-strike',
   'Ground handling strike disrupts cargo flights at Penang airport',
   'A 48-hour strike by ground handling staff at Penang International Airport has delayed outbound cargo, including semiconductor shipments from local assembly plants.',
   'en', TIMESTAMPTZ '2026-10-20 20:40:00+03', TIMESTAMPTZ '2026-10-21 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-21 06:00:00+03',
   'https://example.com/news/2026/10/vietnam-export-controls-electronics',
   'Vietnam tightens export documentation rules for electronics',
   'New certificate-of-origin verification requirements for electronics exports from Vietnam take effect next month, potentially slowing customs clearance for monitors and components.',
   'en', TIMESTAMPTZ '2026-10-20 13:00:00+03', TIMESTAMPTZ '2026-11-10 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-22 06:00:00+03',
   'https://example.com/haber/2026/10/mersin-limani-yogunluk',
   'Mersin Limanı''nda konteyner yoğunluğu: bekleme süreleri uzadı',
   'Mersin Limanı''nda artan ithalat hacmi ve vinç arızası nedeniyle gemi bekleme süreleri ortalama 4 güne çıktı.',
   'tr', TIMESTAMPTZ '2026-10-21 17:30:00+03', TIMESTAMPTZ '2026-10-22 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-22 06:00:00+03',
   'https://example.com/news/2026/10/korea-turkey-fta-ssd-tariff',
   'South Korea and Türkiye agree to cut tariffs on additional IT products',
   'An amendment to the Korea–Türkiye FTA removes remaining duties on a number of IT products, including solid-state drives, starting January 2027.',
   'en', TIMESTAMPTZ '2026-10-21 08:00:00+03', TIMESTAMPTZ '2027-01-01 00:00:00+03'),
  (TIMESTAMPTZ '2026-10-22 06:00:00+03',
   'https://example.com/news/2026/10/intel-core-ultra-price-cut',
   'Intel trims prices of Core Ultra 200S desktop CPUs',
   'Intel reduced list prices for several Core Ultra 200S processors by around 5% ahead of the holiday season.',
   'en', TIMESTAMPTZ '2026-10-21 19:00:00+03', TIMESTAMPTZ '2026-10-25 00:00:00+03')
) AS v(scan_started, url, title, content, lang, published, effective)
JOIN scan_logs sl ON sl.started_at = v.scan_started;

-- =====================================================================
-- ADIM 3: article_analyses  (haberin geldiği taramadaki analizi)
-- =====================================================================
INSERT INTO article_analyses (article_id, scan_log_id, is_relevant, impact_score, event_type, summary,
                                          rate_type, old_rate_pct, new_rate_pct, expected_delay_days, created_at)
SELECT a.id, a.first_seen_scan_id, v.relevant, v.score, v.event, v.summary, v.rate_type, v.old_rate, v.new_rate, v.delay,
       a.published_at + INTERVAL '8 hours'
FROM (VALUES
  ('https://example.com/haber/2026/10/cin-mensheli-guc-kaynaklarina-ilave-gumruk-vergisi',
   TRUE,  78, 'tariff_increase',      'Çin menşeli güç kaynaklarında İGV %11 → %20. FSP güç kaynağı maliyeti artacak.',
   'igv', 11.00, 20.00, NULL),
  ('https://example.com/news/2026/10/red-sea-attacks-suez-diversions',
   TRUE,  85, 'transport_disruption', 'Süveyş Kanalı üzerinden geçen deniz sevkiyatları Ümit Burnu''na yönlendiriliyor; +10-14 gün gecikme.',
   NULL, NULL, NULL, 12),
  ('https://example.com/news/2026/10/local-football-results',
   FALSE, NULL, 'not_relevant',       'Tedarik zinciriyle ilgisiz spor haberi.',
   NULL, NULL, NULL, NULL),
  ('https://example.com/news/2026/10/dram-contract-prices-surge-q4',
   TRUE,  64, 'price_change',         'DDR5 sözleşme fiyatlarında Q4 için ~%15 artış bekleniyor; Kingston bellek maliyeti etkilenecek.',
   NULL, NULL, NULL, NULL),
  ('https://example.com/news/2026/10/kaohsiung-typhoon-port-closure',
   TRUE,  58, 'transport_disruption', 'Kaohsiung Limanı tayfun nedeniyle en az 3 gün kapalı; Noctua soğutucu sevkiyatı gecikebilir.',
   NULL, NULL, NULL, 4),
  ('https://example.com/news/2026/10/nvidia-rtx-5060-supply-shortage',
   TRUE,  70, 'price_change',         'RTX 5060 GPU tahsisatı kısıtlı; ekran kartı fiyatları %8-12 artış eğiliminde.',
   NULL, NULL, NULL, 7),
  ('https://example.com/haber/2026/10/kultur-fonu-orani-degisikligi',
   TRUE,  45, 'tariff_increase',      'Depolama birimlerinde kültür fonu %1 → %2. SSD ithalat maliyeti hafif artacak.',
   'kultur_fonu', 1.00, 2.00, NULL),
  ('https://example.com/news/2026/10/malaysia-penang-airport-strike',
   TRUE,  52, 'transport_disruption', 'Penang Havalimanı''nda 48 saatlik grev; Intel işlemci hava kargosu gecikebilir.',
   NULL, NULL, NULL, 2),
  ('https://example.com/news/2026/10/vietnam-export-controls-electronics',
   TRUE,  40, 'trade_restriction',    'Vietnam elektronik ihracatında menşe belgesi doğrulaması sıkılaşıyor; monitör gümrük işlemleri yavaşlayabilir.',
   NULL, NULL, NULL, 3),
  ('https://example.com/haber/2026/10/mersin-limani-yogunluk',
   TRUE,  55, 'transport_disruption', 'Mersin Limanı''nda bekleme süresi ortalama 4 gün; tüm deniz yolu sevkiyatları etkilenir.',
   NULL, NULL, NULL, 4),
  ('https://example.com/news/2026/10/korea-turkey-fta-ssd-tariff',
   TRUE,  30, 'tariff_decrease',      'Kore-Türkiye STA kapsamında SSD dahil bazı BT ürünlerinde gümrük vergisi 2027''den itibaren sıfırlanıyor.',
   NULL, NULL, NULL, NULL),
  ('https://example.com/news/2026/10/intel-core-ultra-price-cut',
   TRUE,  25, 'price_change',         'Intel Core Ultra 200S işlemcilerde ~%5 liste fiyatı indirimi.',
   NULL, NULL, NULL, NULL)
) AS v(url, relevant, score, event, summary, rate_type, old_rate, new_rate, delay)
JOIN articles a ON a.url = v.url;

-- =====================================================================
-- ADIM 4: article_impacts  (her satır tek bir hedefe işaret eder)
-- hedef türü: country (iso) | location (ad) | supplier (ad) | item (ad)
-- =====================================================================
INSERT INTO article_impacts (article_analysis_id, country_id, location_id, supplier_id, item_id)
SELECT aa.id, c.id, l.id, s.id, i.id
FROM (VALUES
  ('https://example.com/haber/2026/10/cin-mensheli-guc-kaynaklarina-ilave-gumruk-vergisi', 'country',  'CHN'),
  ('https://example.com/haber/2026/10/cin-mensheli-guc-kaynaklarina-ilave-gumruk-vergisi', 'item',     'Güç kaynağı'),
  ('https://example.com/haber/2026/10/cin-mensheli-guc-kaynaklarina-ilave-gumruk-vergisi', 'supplier', 'FSP'),
  ('https://example.com/news/2026/10/red-sea-attacks-suez-diversions',                     'location', 'Süveyş Kanalı'),
  ('https://example.com/news/2026/10/red-sea-attacks-suez-diversions',                     'country',  'EGY'),
  ('https://example.com/news/2026/10/dram-contract-prices-surge-q4',                       'item',     'Bellek'),
  ('https://example.com/news/2026/10/dram-contract-prices-surge-q4',                       'supplier', 'Kingston'),
  ('https://example.com/news/2026/10/kaohsiung-typhoon-port-closure',                      'location', 'Kaohsiung Limanı'),
  ('https://example.com/news/2026/10/kaohsiung-typhoon-port-closure',                      'country',  'TWN'),
  ('https://example.com/news/2026/10/nvidia-rtx-5060-supply-shortage',                     'item',     'Ekran kartı'),
  ('https://example.com/news/2026/10/nvidia-rtx-5060-supply-shortage',                     'supplier', 'ASUS'),
  ('https://example.com/news/2026/10/nvidia-rtx-5060-supply-shortage',                     'supplier', 'Gigabyte'),
  ('https://example.com/haber/2026/10/kultur-fonu-orani-degisikligi',                      'item',     'SSD'),
  ('https://example.com/news/2026/10/malaysia-penang-airport-strike',                      'location', 'Penang Uluslararası Havalimanı'),
  ('https://example.com/news/2026/10/malaysia-penang-airport-strike',                      'supplier', 'Intel'),
  ('https://example.com/news/2026/10/vietnam-export-controls-electronics',                 'country',  'VNM'),
  ('https://example.com/news/2026/10/vietnam-export-controls-electronics',                 'item',     'Monitör'),
  ('https://example.com/haber/2026/10/mersin-limani-yogunluk',                             'location', 'Mersin Limanı'),
  ('https://example.com/news/2026/10/korea-turkey-fta-ssd-tariff',                         'country',  'KOR'),
  ('https://example.com/news/2026/10/korea-turkey-fta-ssd-tariff',                         'item',     'SSD'),
  ('https://example.com/news/2026/10/intel-core-ultra-price-cut',                          'supplier', 'Intel'),
  ('https://example.com/news/2026/10/intel-core-ultra-price-cut',                          'item',     'İşlemci')
) AS v(url, target, ref)
JOIN articles a          ON a.url = v.url
JOIN article_analyses aa ON aa.article_id = a.id
LEFT JOIN countries c    ON v.target = 'country'  AND c.iso_code = v.ref
LEFT JOIN locations l    ON v.target = 'location' AND l.name = v.ref
LEFT JOIN suppliers s    ON v.target = 'supplier' AND s.name = v.ref
LEFT JOIN items i        ON v.target = 'item'     AND i.name = v.ref;

COMMIT;
