-- =====================================================================
-- supply_db — ŞEMA: sadece tablolar ve indeksler (veri yok)
-- Boş bir veritabanında çalıştırılır. Veriler db/data/ klasöründedir.
--
-- Çalıştırma: python db/rebuild_db.py  (şemayı kurar, sonra db/data/ dosyalarını sırayla yükler)
-- ya da elle:
--   docker cp db/supply_db.sql proje_postgres:/tmp/x.sql
--   docker exec proje_postgres psql -U proje_admin -d supply_db -q -v ON_ERROR_STOP=1 -f /tmp/x.sql
-- =====================================================================

BEGIN;

CREATE TABLE countries (
    id          SERIAL PRIMARY KEY,
    iso_code    CHAR(3)      NOT NULL UNIQUE,          -- ISO 3166-1 alpha-3
    name_tr     VARCHAR(100) NOT NULL,
    name_en     VARCHAR(100) NOT NULL,
    has_trade_agreement BOOLEAN NOT NULL DEFAULT FALSE  -- Türkiye ile serbest ticaret anlaşması
);

-- Ports, airports, border gates and chokepoints (straits, canals).
-- Shipment routes reference these, so news about a location can be
-- matched to shipments that pass through it.
CREATE TABLE locations (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    code          VARCHAR(5) UNIQUE,                   -- UN/LOCODE (liman) veya IATA (havalimanı)
    location_type VARCHAR(20)  NOT NULL
                  CHECK (location_type IN ('port','airport','border_gate','chokepoint')),
    country_id    INT REFERENCES countries(id)      -- NULL for international chokepoints
);

-- Oran kaynağı (ör. Ticaret Bakanlığı TARA); items ve tariffs oranlarının nereden alındığı
CREATE TABLE rate_sources (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE,   -- 'TARA (Ticaret Bakanlığı)'
    url   TEXT
);

CREATE TABLE items (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    hs6             CHAR(6)      NOT NULL,             -- international HS code
    gtip            VARCHAR(16)  NOT NULL,           -- Turkish customs tariff code (farklı ürünler aynı GTİP'i paylaşabilir)
    unit            VARCHAR(10)  NOT NULL,             -- kg, pcs, ton,
    kdv_rate        NUMERIC(5,2) NOT NULL DEFAULT 20,  -- VAT %
    otv_rate       NUMERIC(12,4),                     -- % if rate, amount per unit if fixed
    kultur_fonu_rate NUMERIC(5,2) NOT NULL DEFAULT 0,
    gv_rate_base    NUMERIC(5,2),                      -- tercihsiz (taban) Gümrük Vergisi %, STA'sız ülkeye uygulanan
    igv_rate_base   NUMERIC(5,2),                      -- tercihsiz (taban) İlave Gümrük Vergisi %
    source_id       INT REFERENCES rate_sources(id),
    checked_at      DATE                               -- oranın kaynaktan en son kontrol edildiği tarih
);
CREATE INDEX idx_items_hs6 ON items(hs6);

-- Customs duties depend on item AND origin country, and change over time.
CREATE TABLE tariffs (
    id                SERIAL PRIMARY KEY,
    item_id           INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    country_id INT NOT NULL REFERENCES countries(id),
    gv_rate           NUMERIC(5,2) NOT NULL,           -- Gümrük Vergisi %
    igv_rate          NUMERIC(5,2) NOT NULL DEFAULT 0, -- İlave Gümrük Vergisi %
    valid_from        DATE NOT NULL,
    valid_to          DATE,                            -- NULL = currently in force
    source_id         INT REFERENCES rate_sources(id),
    checked_at        DATE,                            -- oranın kaynaktan en son kontrol edildiği tarih
    CHECK (valid_to IS NULL OR valid_to > valid_from),
    UNIQUE (item_id, country_id, valid_from)
);

-- ---------------------------------------------------------------------
-- 2. SUPPLY SIDE
-- ---------------------------------------------------------------------

CREATE TABLE suppliers (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,
    name_original  VARCHAR(200),                       -- name in native script
    country_id     INT NOT NULL REFERENCES countries(id),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_suppliers_country ON suppliers(country_id);

-- Which supplier sells which item (and under which model / SKU).
CREATE TABLE supplier_items (
    id           SERIAL PRIMARY KEY,
    supplier_id  INT NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    item_id      INT NOT NULL REFERENCES items(id),
    item_model   VARCHAR(100) NOT NULL DEFAULT '',
    assembly_country_id INT REFERENCES countries(id),  -- birleştirme ülkesi
    annual_quantity     INT CHECK (annual_quantity >= 0),  -- yılda alınan adet (Görev 3 maliyet hesabı)
    UNIQUE (supplier_id, item_id, item_model)
);
CREATE INDEX idx_supplier_items_item ON supplier_items(item_id);

CREATE TABLE contracts (
    id                SERIAL PRIMARY KEY,
    supplier_item_id  INT NOT NULL REFERENCES supplier_items(id),
    start_date        DATE NOT NULL,
    end_date          DATE,
    currency          CHAR(3) NOT NULL,                -- ISO 4217
    purchase_amount          NUMERIC(14,3),                   
    unit_price        NUMERIC(14,4) NOT NULL,
    contract_date        DATE,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
CREATE INDEX idx_contracts_supplier_item ON contracts(supplier_item_id);

CREATE TABLE shipments (
    id                       SERIAL PRIMARY KEY,
    contract_id              INT NOT NULL REFERENCES contracts(id),
    transport_mode           VARCHAR(10) NOT NULL
                             CHECK (transport_mode IN ('sea','air','road')),
    origin_country_id        INT NOT NULL REFERENCES countries(id),  -- menşei
    exit_location_id         INT REFERENCES locations(id),
    destination_location_id  INT REFERENCES locations(id),
    status                   VARCHAR(15) NOT NULL DEFAULT 'planned'
                             CHECK (status IN ('planned','in_transit','delayed','arrived','cancelled')),
    expected_transit_days    INT
);
CREATE INDEX idx_shipments_contract ON shipments(contract_id);
CREATE INDEX idx_shipments_status   ON shipments(status);

CREATE TABLE inventory (
    id                SERIAL PRIMARY KEY,
    supplier_item_id  INT NOT NULL UNIQUE REFERENCES supplier_items(id),
    on_hand           NUMERIC(14,3) NOT NULL DEFAULT 0,
    reserved          NUMERIC(14,3) NOT NULL DEFAULT 0,
    reorder_point     NUMERIC(14,3),                   
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (reserved <= on_hand)
);

-- ---------------------------------------------------------------------
-- 3. NEWS / RISK SIDE
-- ---------------------------------------------------------------------

CREATE TABLE scan_logs (
    id             SERIAL PRIMARY KEY,
    triggered_by   VARCHAR(20) NOT NULL
                   CHECK (triggered_by IN ('schedule','manual')),
    status         VARCHAR(10) NOT NULL DEFAULT 'running'
                   CHECK (status IN ('running','success','failed')),
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    error_message  TEXT,
    -- tarama özeti
    query_count    INT CHECK (query_count >= 0),
    found_count    INT CHECK (found_count >= 0),
    rejected_count INT CHECK (rejected_count >= 0),
    error_count    INT CHECK (error_count >= 0)
);

CREATE TABLE articles (
    id                  SERIAL PRIMARY KEY,
    first_seen_scan_id  INT NOT NULL REFERENCES scan_logs(id),   -- haberi ilk getiren tarama (eski scan_log_id)
    last_seen_scan_id   INT NOT NULL REFERENCES scan_logs(id),   -- haberin en son görüldüğü tarama
    url                 TEXT NOT NULL UNIQUE,                    -- aynı URL tekrar eklenmez
    content_hash        CHAR(64) NOT NULL,                       -- sha256(normalize(title + content)), hex
    title               TEXT NOT NULL,
    content             TEXT,
    language            CHAR(2),                                 -- ISO 639-1
    published_at        TIMESTAMPTZ,
    effective_date      TIMESTAMPTZ,                             -- kararın / olayın yürürlük tarihi
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),      -- içerik (hash) en son ne zaman değişti
    CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    CHECK (last_seen_scan_id >= first_seen_scan_id)
);
CREATE INDEX idx_articles_published ON articles(published_at);
CREATE INDEX idx_articles_hash      ON articles(content_hash);   -- farklı URL'de aynı metin (ajans haberleri)
CREATE INDEX idx_articles_last_seen ON articles(last_seen_scan_id);

-- Her taramada her haber için bir analiz satırı (eski analizler silinmez,
-- böylece "skor değişti mi?" sorusu cevaplanabilir). En güncel analiz = en büyük scan_log_id.
CREATE TABLE article_analyses (
    id                   SERIAL PRIMARY KEY,
    article_id           INT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    scan_log_id          INT NOT NULL REFERENCES scan_logs(id) ON DELETE CASCADE,
    is_relevant          BOOLEAN NOT NULL,
    impact_score         SMALLINT CHECK (impact_score BETWEEN 1 AND 100),
    event_type           VARCHAR(30)
                         CHECK (event_type IN ('tariff_increase','tariff_decrease','trade_restriction',
                                               'transport_disruption', 'price_change','not_relevant','other')),
    summary              TEXT,
    rate_type  VARCHAR(20)
           CHECK (rate_type IN ('gv', 'igv', 'kultur_fonu', 'kdv', 'otv')),
    old_rate_pct         NUMERIC(6,2),
    new_rate_pct         NUMERIC(6,2),
    price_change_pct     NUMERIC(6,2),                -- fiyat değişimi % (event_type = 'price_change')
    expected_delay_days  INT CHECK (expected_delay_days >= 0),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (article_id, scan_log_id)                 -- aynı haber aynı taramada bir kez analiz edilir
);
CREATE INDEX idx_analyses_scan ON article_analyses(scan_log_id);

-- What the article affects. This is the link between news and supply.
-- Each row points at exactly one target.
CREATE TABLE article_impacts (
    id                   SERIAL PRIMARY KEY,
    article_analysis_id  INT NOT NULL REFERENCES article_analyses(id) ON DELETE CASCADE,
    country_id           INT REFERENCES countries(id),
    location_id          INT REFERENCES locations(id),
    supplier_id          INT REFERENCES suppliers(id),
    item_id              INT REFERENCES items(id),
    CHECK (num_nonnulls(country_id, location_id, supplier_id, item_id) = 1)
);
CREATE INDEX idx_impacts_analysis ON article_impacts(article_analysis_id);
CREATE INDEX idx_impacts_country  ON article_impacts(country_id);
CREATE INDEX idx_impacts_location ON article_impacts(location_id);
CREATE INDEX idx_impacts_supplier ON article_impacts(supplier_id);
CREATE INDEX idx_impacts_item     ON article_impacts(item_id);

-- Görev 3: maliyet etkisi. Her analiz için bir satır; aynı analiz tekrar
-- hesaplanırsa satır güncellenir (ON CONFLICT (article_analysis_id) DO UPDATE).
-- Çalışma sırası: tarama → article_analyses → cost_impacts → alerts
-- alerts ile bağlantı: cost_impacts.article_analysis_id = alerts.latest_analysis_id
CREATE TABLE cost_impacts (
    id                   SERIAL PRIMARY KEY,
    article_analysis_id  INT NOT NULL UNIQUE REFERENCES article_analyses(id) ON DELETE CASCADE,
    status               VARCHAR(15) NOT NULL CHECK (status IN ('hesaplandi', 'hesaplanamadi')),  -- hesaplanamadi → nedeni reason'da
    calc_type            VARCHAR(30) NOT NULL,         -- vergi_degisikligi / lojistik_gecikme / fiyat_degisikligi (haberin türü değil; trade_restriction → lojistik_gecikme)
    direction            VARCHAR(20),                  -- artis / azalis / parasal_etki_yok / etkilenen_yok
    annual_diff_usd      NUMERIC(14,2),                -- yıllık maliyet farkı
    year_end_diff_usd    NUMERIC(14,2),                -- yürürlük tarihinden 31 Aralık'a kadarki fark
    per_pc_diff_usd      NUMERIC(10,2),                -- bilgisayar başına fark
    cost_share_pct       NUMERIC(8,2),                 -- yıllık fark / toplam yıllık parça maliyeti (vergiler dahil) × 100
    stock_status         VARCHAR(15),                  -- etkilenen parçalardaki en kötü durum: yetersiz / sinira_yakin / yeterli
    stop_days            NUMERIC(6,1),                 -- üretimin duracağı gün (0 = durmuyor)
    unbuilt_pc           INT,                          -- üretilemeyecek bilgisayar sayısı
    duration_unknown     BOOLEAN,                      -- gecikme süresi haberde yoksa true
    is_draft             BOOLEAN NOT NULL,             -- puan 66–79
    is_unconfirmed       BOOLEAN NOT NULL,             -- puan 65 ve altı
    affected_item_ids    INT[] NOT NULL DEFAULT '{}',  -- items.id
    message              TEXT,                         -- panelde gösterilecek sonuç cümlesi (İngilizce)
    reason               TEXT,                         -- hesaplanamama nedeni
    warnings             TEXT[] NOT NULL DEFAULT '{}',
    calculated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 4. ALERTS (Görev 4: hafıza ve değişiklik tespiti)
-- ---------------------------------------------------------------------
-- articles / article_analyses = "hangi haberde ne yazıyor"  (ham bilgi, haber başına)
-- alerts                      = "şirketimiz için hangi RİSK var" (panelde görünen kart, risk başına)
--
-- Aynı risk birden fazla haberde geçebilir. Örnek:
--   Haber A (Reuters):  "Mersin Limanı'nda gemiler 4 gün bekliyor"
--   Haber B (Bloomberg):"Mersin'de konteyner yoğunluğu rekor seviyede"
--   Haber C (AA):       "Liman yoğunluğu ithalatı geciktiriyor"
-- Üçü de aynı riski anlatıyor: transport_disruption + Mersin Limanı.
-- Panelde 3 ayrı kart yerine 1 alert gösterilir; A, B, C bu alert'in kaynaklarıdır
-- (bağlantı alert_articles tablosunda tutulur).
--
-- Risk kimliği = olay türü + etkilenen tek hedef (ülke / lokasyon / tedarikçi / ürün).
-- Bu ikili risk_key sütununda otomatik üretilir, ör. 'transport_disruption:location:10'.
--
-- Her taramada her alert'in durumu güncellenir:
--   new       → bu risk ilk kez görüldü
--   changed   → risk önceden vardı ama skor / oran / gecikme değişti ya da yeni kaynak geldi
--   unchanged → risk hâlâ var, değişen bir şey yok (bildirim gönderilmez)
--   resolved  → risk son N başarılı taramada hiç görülmedi, kapandı
CREATE TABLE alerts (
    id                  SERIAL PRIMARY KEY,

    -- Riskin ne olduğu: olay türü + tek hedef (article_impacts ile aynı mantık)
    event_type          VARCHAR(30) NOT NULL
                        CHECK (event_type IN ('tariff_increase','tariff_decrease','trade_restriction',
                                              'transport_disruption','price_change','other')),
    country_id          INT REFERENCES countries(id),
    location_id         INT REFERENCES locations(id),
    supplier_id         INT REFERENCES suppliers(id),
    item_id             INT REFERENCES items(id),
    CHECK (num_nonnulls(country_id, location_id, supplier_id, item_id) = 1),

    -- Otomatik hesaplanır, elle yazılmaz. Aynı riski bulmak için kullanılır.
    risk_key            TEXT GENERATED ALWAYS AS (
                            event_type || ':' ||
                            CASE
                              WHEN supplier_id IS NOT NULL THEN 'supplier:' || supplier_id::text
                              WHEN item_id     IS NOT NULL THEN 'item:'     || item_id::text
                              WHEN location_id IS NOT NULL THEN 'location:' || location_id::text
                              ELSE                              'country:'  || country_id::text
                            END
                        ) STORED,

    -- 4.3: değişiklik durumu
    status              VARCHAR(10) NOT NULL DEFAULT 'new'
                        CHECK (status IN ('new','changed','unchanged','resolved')),
    change_reason       TEXT,                             -- ör. 'impact_score 58 → 72', 'İGV %11 → %20'

    -- 4.4: önem
    current_score       SMALLINT CHECK (current_score BETWEEN 1 AND 100),  -- son taramadaki impact_score
    prev_score          SMALLINT CHECK (prev_score    BETWEEN 1 AND 100),  -- bir önceki taramadaki
    -- sıralama puanı: skor × maliyet payı (cost_impacts.cost_share_pct) × yenilik.
    -- Gecikme haberlerinde (calc_type = 'lojistik_gecikme') maliyet payı 0'dır;
    -- bunlarda maliyet payı yerine stop_days / unbuilt_pc / stock_status kullanılır.
    priority_score      NUMERIC(8,2),
    severity            VARCHAR(6) NOT NULL
                        CHECK (severity IN ('low','medium','high')),       -- eşikler Görev 4'te belirlenir (Görev 3.4 yapılmayacak)

    -- Ne zaman görüldü
    latest_analysis_id  INT REFERENCES article_analyses(id) ON DELETE SET NULL,  -- kartta gösterilecek özet
    first_seen_scan_id  INT NOT NULL REFERENCES scan_logs(id),
    last_seen_scan_id   INT NOT NULL REFERENCES scan_logs(id),
    resolved_scan_id    INT REFERENCES scan_logs(id),     -- sadece status = 'resolved' iken dolu

    -- Panel ve bildirim (Görev 5.3, 6.3)
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,   -- kullanıcı kartı gördü mü
    read_at             TIMESTAMPTZ,
    notified_at         TIMESTAMPTZ,                      -- e-posta / bildirim gönderildi mi
    panel_synced_at     TIMESTAMPTZ,                      -- panele olay olarak gönderildi mi (panel_sync.py)

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CHECK ((status = 'resolved') = (resolved_scan_id IS NOT NULL)),
    CHECK (last_seen_scan_id >= first_seen_scan_id)
);

-- Aynı risk için aynı anda yalnızca BİR açık alert olabilir.
-- Risk kapanıp (resolved) sonra yeniden ortaya çıkarsa yeni satır açılır.
CREATE UNIQUE INDEX uq_alerts_open_risk ON alerts(risk_key) WHERE status <> 'resolved';
CREATE INDEX idx_alerts_status   ON alerts(status);
CREATE INDEX idx_alerts_priority ON alerts(priority_score DESC) WHERE status <> 'resolved';
CREATE INDEX idx_alerts_supplier ON alerts(supplier_id);
CREATE INDEX idx_alerts_location ON alerts(location_id);

-- Bir alert'i hangi haberler destekliyor? (çoka-çok bağlantı tablosu)
-- Bir alert'in birden fazla haberi olabilir (yukarıdaki A, B, C örneği),
-- bir haber de birden fazla alert'e kaynak olabilir
-- (ör. "Çin'e ek vergi" haberi hem FSP hem Cooler Master alert'ini besler).
-- Uyarı kartındaki kaynak linkleri buradan gelir (Görev 5.3, 7.2 kaynak doğrulama).
CREATE TABLE alert_articles (
    alert_id            INT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    article_id          INT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    added_scan_id       INT NOT NULL REFERENCES scan_logs(id),   -- bu kaynak hangi taramada eklendi
    PRIMARY KEY (alert_id, article_id)
);
CREATE INDEX idx_alert_articles_article ON alert_articles(article_id);

-- Panel için hazır sorgu: açık alert'ler önem sırasına göre
--   SELECT a.*, aa.summary
--   FROM alerts a LEFT JOIN article_analyses aa ON aa.id = a.latest_analysis_id
--   WHERE a.status <> 'resolved'
--   ORDER BY a.priority_score DESC NULLS LAST;

COMMIT;
