CREATE DATABASE supply_db

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

CREATE TABLE items (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    hs6             CHAR(6)      NOT NULL,             -- international HS code
    gtip            VARCHAR(16)  NOT NULL,           -- Turkish customs tariff code (farklı ürünler aynı GTİP'i paylaşabilir)
    unit            VARCHAR(10)  NOT NULL,             -- kg, pcs, ton,
    kdv_rate        NUMERIC(5,2) NOT NULL DEFAULT 20,  -- VAT %
    otv_rate       NUMERIC(12,4),                     -- % if rate, amount per unit if fixed
    kultur_fonu_rate NUMERIC(5,2) NOT NULL DEFAULT 0
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
    chokepoint_location_id   INT REFERENCES locations(id),           -- Süveyş Kanalı vb.
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
    error_message  TEXT
);

CREATE TABLE articles (
    id            SERIAL PRIMARY KEY,
    scan_log_id   INT NOT NULL REFERENCES scan_logs(id),
    url           TEXT NOT NULL UNIQUE,                -- dedupe across scans
    title         TEXT NOT NULL,
    content       TEXT,
    language      CHAR(2),                             -- ISO 639-1
    published_at  TIMESTAMPTZ,
    affective_date     TIMESTAMPTZ
);
CREATE INDEX idx_articles_published ON articles(published_at);

-- One analysis per article (re-analysis overwrites).
CREATE TABLE article_analyses (
    id                   SERIAL PRIMARY KEY,
    article_id           INT NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
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
    expected_delay_days  INT CHECK (expected_delay_days >= 0),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

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


-- oran kaynağı ticaret bakanlığı
CREATE TABLE rate_sources (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE,   -- 'TARA (Ticaret Bakanlığı)'
    url   TEXT
);

ALTER TABLE tariffs ADD COLUMN source_id  INT REFERENCES rate_sources(id);
ALTER TABLE tariffs ADD COLUMN checked_at DATE;   -- oranın kaynaktan en son kontrol edildiği tarih

ALTER TABLE items   ADD COLUMN source_id  INT REFERENCES rate_sources(id);
ALTER TABLE items   ADD COLUMN checked_at DATE;