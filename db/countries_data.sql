-- countries: 50 ülke, ID'ler otomatik atanır
-- has_trade_agreement = TRUE: Türkiye ile yürürlükte STA veya Gümrük Birliği (AB) var
-- Kaynak: T.C. Ticaret Bakanlığı, yürürlükteki STA listesi (Ekim 2026)

INSERT INTO countries (iso_code, name_tr, name_en, has_trade_agreement) VALUES
  -- ilk 6
  ('MYS', 'Malezya',                    'Malaysia',               TRUE),
  ('KOR', 'Güney Kore',                 'South Korea',            TRUE),
  ('TWN', 'Tayvan',                     'Taiwan',                 FALSE),
  ('CHN', 'Çin',                        'China',                  FALSE),
  ('VNM', 'Vietnam',                    'Vietnam',                FALSE),
  ('TUR', 'Türkiye',                    'Türkiye',                FALSE),

  -- Asya-Pasifik
  ('JPN', 'Japonya',                    'Japan',                  FALSE),
  ('THA', 'Tayland',                    'Thailand',               FALSE),
  ('IDN', 'Endonezya',                  'Indonesia',              FALSE),
  ('PHL', 'Filipinler',                 'Philippines',            FALSE),
  ('IND', 'Hindistan',                  'India',                  FALSE),
  ('SGP', 'Singapur',                   'Singapore',              TRUE),
  ('HKG', 'Hong Kong',                  'Hong Kong',              FALSE),
  ('BGD', 'Bangladeş',                  'Bangladesh',             FALSE),
  ('KHM', 'Kamboçya',                   'Cambodia',               FALSE),
  ('AUS', 'Avustralya',                 'Australia',              FALSE),

  -- Amerika
  ('USA', 'Amerika Birleşik Devletleri', 'United States',         FALSE),
  ('CAN', 'Kanada',                     'Canada',                 FALSE),
  ('MEX', 'Meksika',                    'Mexico',                 FALSE),
  ('BRA', 'Brezilya',                   'Brazil',                 FALSE),
  ('CHL', 'Şili',                       'Chile',                  TRUE),

  -- Avrupa Birliği (Gümrük Birliği)
  ('DEU', 'Almanya',                    'Germany',                TRUE),
  ('NLD', 'Hollanda',                   'Netherlands',            TRUE),
  ('FRA', 'Fransa',                     'France',                 TRUE),
  ('ITA', 'İtalya',                     'Italy',                  TRUE),
  ('ESP', 'İspanya',                    'Spain',                  TRUE),
  ('POL', 'Polonya',                    'Poland',                 TRUE),
  ('CZE', 'Çekya',                      'Czechia',                TRUE),
  ('HUN', 'Macaristan',                 'Hungary',                TRUE),
  ('ROU', 'Romanya',                    'Romania',                TRUE),
  ('IRL', 'İrlanda',                    'Ireland',                TRUE),
  ('SWE', 'İsveç',                      'Sweden',                 TRUE),
  ('AUT', 'Avusturya',                  'Austria',                TRUE),

  -- Diğer Avrupa
  ('GBR', 'Birleşik Krallık',           'United Kingdom',         TRUE),
  ('CHE', 'İsviçre',                    'Switzerland',            TRUE),   -- EFTA
  ('NOR', 'Norveç',                     'Norway',                 TRUE),   -- EFTA
  ('UKR', 'Ukrayna',                    'Ukraine',                TRUE),   -- 01.10.2026 yürürlükte, gümrük indirimleri 01.01.2027
  ('MDA', 'Moldova',                    'Moldova',                TRUE),
  ('SRB', 'Sırbistan',                  'Serbia',                 TRUE),
  ('MKD', 'Kuzey Makedonya',            'North Macedonia',        TRUE),
  ('BIH', 'Bosna-Hersek',               'Bosnia and Herzegovina', TRUE),
  ('ALB', 'Arnavutluk',                 'Albania',                TRUE),
  ('GEO', 'Gürcistan',                  'Georgia',                TRUE),
  ('AZE', 'Azerbaycan',                 'Azerbaijan',             FALSE),  -- tercihli ticaret anlaşması, STA değil

  -- Orta Doğu ve Afrika
  ('ARE', 'Birleşik Arap Emirlikleri',  'United Arab Emirates',   TRUE),
  ('QAT', 'Katar',                      'Qatar',                  TRUE),
  ('SAU', 'Suudi Arabistan',            'Saudi Arabia',           FALSE),
  ('EGY', 'Mısır',                      'Egypt',                  TRUE),
  ('MAR', 'Fas',                        'Morocco',                TRUE),
  ('TUN', 'Tunus',                      'Tunisia',                TRUE);
