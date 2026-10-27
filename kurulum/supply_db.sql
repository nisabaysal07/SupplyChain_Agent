--
-- PostgreSQL database dump
--

\restrict Ejyfbilplc7JJGm238TOWObfsMefHKP2ArrPQHmK2tWhXPb4R7BCcwYTgQGqu0z

-- Dumped from database version 17.11 (Debian 17.11-1.pgdg13+2)
-- Dumped by pg_dump version 17.11 (Debian 17.11-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alert_articles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_articles (
    alert_id integer NOT NULL,
    article_id integer NOT NULL,
    added_scan_id integer NOT NULL
);


--
-- Name: alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alerts (
    id integer NOT NULL,
    event_type character varying(30) NOT NULL,
    country_id integer,
    location_id integer,
    supplier_id integer,
    item_id integer,
    risk_key text GENERATED ALWAYS AS ((((event_type)::text || ':'::text) ||
CASE
    WHEN (supplier_id IS NOT NULL) THEN ('supplier:'::text || (supplier_id)::text)
    WHEN (item_id IS NOT NULL) THEN ('item:'::text || (item_id)::text)
    WHEN (location_id IS NOT NULL) THEN ('location:'::text || (location_id)::text)
    ELSE ('country:'::text || (country_id)::text)
END)) STORED,
    status character varying(10) DEFAULT 'new'::character varying NOT NULL,
    change_reason text,
    current_score smallint,
    prev_score smallint,
    priority_score numeric(8,2),
    severity character varying(6) NOT NULL,
    latest_analysis_id integer,
    first_seen_scan_id integer NOT NULL,
    last_seen_scan_id integer NOT NULL,
    resolved_scan_id integer,
    is_read boolean DEFAULT false NOT NULL,
    read_at timestamp with time zone,
    notified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT alerts_check CHECK ((num_nonnulls(country_id, location_id, supplier_id, item_id) = 1)),
    CONSTRAINT alerts_check1 CHECK ((((status)::text = 'resolved'::text) = (resolved_scan_id IS NOT NULL))),
    CONSTRAINT alerts_check2 CHECK ((last_seen_scan_id >= first_seen_scan_id)),
    CONSTRAINT alerts_current_score_check CHECK (((current_score >= 1) AND (current_score <= 100))),
    CONSTRAINT alerts_event_type_check CHECK (((event_type)::text = ANY ((ARRAY['tariff_increase'::character varying, 'tariff_decrease'::character varying, 'trade_restriction'::character varying, 'transport_disruption'::character varying, 'price_change'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT alerts_prev_score_check CHECK (((prev_score >= 1) AND (prev_score <= 100))),
    CONSTRAINT alerts_severity_check CHECK (((severity)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[]))),
    CONSTRAINT alerts_status_check CHECK (((status)::text = ANY ((ARRAY['new'::character varying, 'changed'::character varying, 'unchanged'::character varying, 'resolved'::character varying])::text[])))
);


--
-- Name: alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alerts_id_seq OWNED BY public.alerts.id;


--
-- Name: article_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.article_analyses (
    id integer NOT NULL,
    article_id integer NOT NULL,
    scan_log_id integer NOT NULL,
    is_relevant boolean NOT NULL,
    impact_score smallint,
    event_type character varying(30),
    summary text,
    rate_type character varying(20),
    old_rate_pct numeric(6,2),
    new_rate_pct numeric(6,2),
    expected_delay_days integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT article_analyses_event_type_check CHECK (((event_type)::text = ANY ((ARRAY['tariff_increase'::character varying, 'tariff_decrease'::character varying, 'trade_restriction'::character varying, 'transport_disruption'::character varying, 'price_change'::character varying, 'not_relevant'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT article_analyses_expected_delay_days_check CHECK ((expected_delay_days >= 0)),
    CONSTRAINT article_analyses_impact_score_check CHECK (((impact_score >= 1) AND (impact_score <= 100))),
    CONSTRAINT article_analyses_rate_type_check CHECK (((rate_type)::text = ANY ((ARRAY['gv'::character varying, 'igv'::character varying, 'kultur_fonu'::character varying, 'kdv'::character varying, 'otv'::character varying])::text[])))
);


--
-- Name: article_analyses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.article_analyses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: article_analyses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.article_analyses_id_seq OWNED BY public.article_analyses.id;


--
-- Name: article_impacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.article_impacts (
    id integer NOT NULL,
    article_analysis_id integer NOT NULL,
    country_id integer,
    location_id integer,
    supplier_id integer,
    item_id integer,
    CONSTRAINT article_impacts_check CHECK ((num_nonnulls(country_id, location_id, supplier_id, item_id) = 1))
);


--
-- Name: article_impacts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.article_impacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: article_impacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.article_impacts_id_seq OWNED BY public.article_impacts.id;


--
-- Name: articles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.articles (
    id integer NOT NULL,
    first_seen_scan_id integer NOT NULL,
    last_seen_scan_id integer NOT NULL,
    url text NOT NULL,
    content_hash character(64) NOT NULL,
    title text NOT NULL,
    content text,
    language character(2),
    published_at timestamp with time zone,
    effective_date timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT articles_check CHECK ((last_seen_scan_id >= first_seen_scan_id)),
    CONSTRAINT articles_content_hash_check CHECK ((content_hash ~ '^[0-9a-f]{64}$'::text))
);


--
-- Name: articles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.articles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: articles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.articles_id_seq OWNED BY public.articles.id;


--
-- Name: contracts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contracts (
    id integer NOT NULL,
    supplier_item_id integer NOT NULL,
    start_date date NOT NULL,
    end_date date,
    currency character(3) NOT NULL,
    purchase_amount numeric(14,3),
    unit_price numeric(14,4) NOT NULL,
    contract_date date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT contracts_check CHECK (((end_date IS NULL) OR (end_date >= start_date)))
);


--
-- Name: contracts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contracts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contracts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contracts_id_seq OWNED BY public.contracts.id;


--
-- Name: countries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.countries (
    id integer NOT NULL,
    iso_code character(3) NOT NULL,
    name_tr character varying(100) NOT NULL,
    name_en character varying(100) NOT NULL,
    has_trade_agreement boolean DEFAULT false NOT NULL
);


--
-- Name: countries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.countries_id_seq OWNED BY public.countries.id;


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    id integer NOT NULL,
    supplier_item_id integer NOT NULL,
    on_hand numeric(14,3) DEFAULT 0 NOT NULL,
    reserved numeric(14,3) DEFAULT 0 NOT NULL,
    reorder_point numeric(14,3),
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT inventory_check CHECK ((reserved <= on_hand))
);


--
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- Name: items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.items (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    hs6 character(6) NOT NULL,
    gtip character varying(16) NOT NULL,
    unit character varying(10) NOT NULL,
    kdv_rate numeric(5,2) DEFAULT 20 NOT NULL,
    otv_rate numeric(12,4),
    kultur_fonu_rate numeric(5,2) DEFAULT 0 NOT NULL,
    source_id integer,
    checked_at date
);


--
-- Name: items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.items_id_seq OWNED BY public.items.id;


--
-- Name: locations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.locations (
    id integer NOT NULL,
    name character varying(150) NOT NULL,
    code character varying(5),
    location_type character varying(20) NOT NULL,
    country_id integer,
    CONSTRAINT locations_location_type_check CHECK (((location_type)::text = ANY ((ARRAY['port'::character varying, 'airport'::character varying, 'border_gate'::character varying, 'chokepoint'::character varying])::text[])))
);


--
-- Name: locations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.locations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: locations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.locations_id_seq OWNED BY public.locations.id;


--
-- Name: rate_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rate_sources (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    url text
);


--
-- Name: rate_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rate_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rate_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rate_sources_id_seq OWNED BY public.rate_sources.id;


--
-- Name: scan_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scan_logs (
    id integer NOT NULL,
    triggered_by character varying(20) NOT NULL,
    status character varying(10) DEFAULT 'running'::character varying NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    finished_at timestamp with time zone,
    error_message text,
    CONSTRAINT scan_logs_status_check CHECK (((status)::text = ANY ((ARRAY['running'::character varying, 'success'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT scan_logs_triggered_by_check CHECK (((triggered_by)::text = ANY ((ARRAY['schedule'::character varying, 'manual'::character varying])::text[])))
);


--
-- Name: scan_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scan_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scan_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scan_logs_id_seq OWNED BY public.scan_logs.id;


--
-- Name: shipments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipments (
    id integer NOT NULL,
    contract_id integer NOT NULL,
    transport_mode character varying(10) NOT NULL,
    origin_country_id integer NOT NULL,
    exit_location_id integer,
    destination_location_id integer,
    status character varying(15) DEFAULT 'planned'::character varying NOT NULL,
    expected_transit_days integer,
    CONSTRAINT shipments_status_check CHECK (((status)::text = ANY ((ARRAY['planned'::character varying, 'in_transit'::character varying, 'delayed'::character varying, 'arrived'::character varying, 'cancelled'::character varying])::text[]))),
    CONSTRAINT shipments_transport_mode_check CHECK (((transport_mode)::text = ANY ((ARRAY['sea'::character varying, 'air'::character varying, 'road'::character varying])::text[])))
);


--
-- Name: shipments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shipments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shipments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shipments_id_seq OWNED BY public.shipments.id;


--
-- Name: supplier_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.supplier_items (
    id integer NOT NULL,
    supplier_id integer NOT NULL,
    item_id integer NOT NULL,
    item_model character varying(100) DEFAULT ''::character varying NOT NULL,
    assembly_country_id integer
);


--
-- Name: supplier_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.supplier_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: supplier_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.supplier_items_id_seq OWNED BY public.supplier_items.id;


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suppliers (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    name_original character varying(200),
    country_id integer NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: suppliers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.suppliers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: suppliers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.suppliers_id_seq OWNED BY public.suppliers.id;


--
-- Name: tariffs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tariffs (
    id integer NOT NULL,
    item_id integer NOT NULL,
    country_id integer NOT NULL,
    gv_rate numeric(5,2) NOT NULL,
    igv_rate numeric(5,2) DEFAULT 0 NOT NULL,
    valid_from date NOT NULL,
    valid_to date,
    source_id integer,
    checked_at date,
    CONSTRAINT tariffs_check CHECK (((valid_to IS NULL) OR (valid_to > valid_from)))
);


--
-- Name: tariffs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tariffs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tariffs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tariffs_id_seq OWNED BY public.tariffs.id;


--
-- Name: alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts ALTER COLUMN id SET DEFAULT nextval('public.alerts_id_seq'::regclass);


--
-- Name: article_analyses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses ALTER COLUMN id SET DEFAULT nextval('public.article_analyses_id_seq'::regclass);


--
-- Name: article_impacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts ALTER COLUMN id SET DEFAULT nextval('public.article_impacts_id_seq'::regclass);


--
-- Name: articles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles ALTER COLUMN id SET DEFAULT nextval('public.articles_id_seq'::regclass);


--
-- Name: contracts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts ALTER COLUMN id SET DEFAULT nextval('public.contracts_id_seq'::regclass);


--
-- Name: countries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries ALTER COLUMN id SET DEFAULT nextval('public.countries_id_seq'::regclass);


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- Name: items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items ALTER COLUMN id SET DEFAULT nextval('public.items_id_seq'::regclass);


--
-- Name: locations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations ALTER COLUMN id SET DEFAULT nextval('public.locations_id_seq'::regclass);


--
-- Name: rate_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rate_sources ALTER COLUMN id SET DEFAULT nextval('public.rate_sources_id_seq'::regclass);


--
-- Name: scan_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scan_logs ALTER COLUMN id SET DEFAULT nextval('public.scan_logs_id_seq'::regclass);


--
-- Name: shipments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments ALTER COLUMN id SET DEFAULT nextval('public.shipments_id_seq'::regclass);


--
-- Name: supplier_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_items ALTER COLUMN id SET DEFAULT nextval('public.supplier_items_id_seq'::regclass);


--
-- Name: suppliers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers ALTER COLUMN id SET DEFAULT nextval('public.suppliers_id_seq'::regclass);


--
-- Name: tariffs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs ALTER COLUMN id SET DEFAULT nextval('public.tariffs_id_seq'::regclass);


--
-- Data for Name: alert_articles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alert_articles (alert_id, article_id, added_scan_id) FROM stdin;
\.


--
-- Data for Name: alerts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alerts (id, event_type, country_id, location_id, supplier_id, item_id, status, change_reason, current_score, prev_score, priority_score, severity, latest_analysis_id, first_seen_scan_id, last_seen_scan_id, resolved_scan_id, is_read, read_at, notified_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: article_analyses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.article_analyses (id, article_id, scan_log_id, is_relevant, impact_score, event_type, summary, rate_type, old_rate_pct, new_rate_pct, expected_delay_days, created_at) FROM stdin;
1	1	1	f	\N	not_relevant	Tedarik zinciriyle ilgisiz spor haberi.	\N	\N	\N	\N	2026-10-18 02:00:00+00
2	2	1	t	85	transport_disruption	Süveyş Kanalı üzerinden geçen deniz sevkiyatları Ümit Burnu'na yönlendiriliyor; +10-14 gün gecikme.	\N	\N	\N	12	2026-10-17 20:10:00+00
3	3	1	t	78	tariff_increase	Çin menşeli güç kaynaklarında İGV %11 → %20. FSP güç kaynağı maliyeti artacak.	igv	11.00	20.00	\N	2026-10-18 04:30:00+00
4	4	2	t	58	transport_disruption	Kaohsiung Limanı tayfun nedeniyle en az 3 gün kapalı; Noctua soğutucu sevkiyatı gecikebilir.	\N	\N	\N	4	2026-10-18 23:20:00+00
5	5	2	t	64	price_change	DDR5 sözleşme fiyatlarında Q4 için ~%15 artış bekleniyor; Kingston bellek maliyeti etkilenecek.	\N	\N	\N	\N	2026-10-18 15:45:00+00
6	6	4	t	45	tariff_increase	Depolama birimlerinde kültür fonu %1 → %2. SSD ithalat maliyeti hafif artacak.	kultur_fonu	1.00	2.00	\N	2026-10-20 16:15:00+00
7	7	4	t	70	price_change	RTX 5060 GPU tahsisatı kısıtlı; ekran kartı fiyatları %8-12 artış eğiliminde.	\N	\N	\N	7	2026-10-20 14:00:00+00
8	8	5	t	40	trade_restriction	Vietnam elektronik ihracatında menşe belgesi doğrulaması sıkılaşıyor; monitör gümrük işlemleri yavaşlayabilir.	\N	\N	\N	3	2026-10-20 18:00:00+00
9	9	5	t	52	transport_disruption	Penang Havalimanı'nda 48 saatlik grev; Intel işlemci hava kargosu gecikebilir.	\N	\N	\N	2	2026-10-21 01:40:00+00
10	10	6	t	25	price_change	Intel Core Ultra 200S işlemcilerde ~%5 liste fiyatı indirimi.	\N	\N	\N	\N	2026-10-22 00:00:00+00
11	11	6	t	30	tariff_decrease	Kore-Türkiye STA kapsamında SSD dahil bazı BT ürünlerinde gümrük vergisi 2027'den itibaren sıfırlanıyor.	\N	\N	\N	\N	2026-10-21 13:00:00+00
12	12	6	t	55	transport_disruption	Mersin Limanı'nda bekleme süresi ortalama 4 gün; tüm deniz yolu sevkiyatları etkilenir.	\N	\N	\N	4	2026-10-21 22:30:00+00
\.


--
-- Data for Name: article_impacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.article_impacts (id, article_analysis_id, country_id, location_id, supplier_id, item_id) FROM stdin;
1	9	\N	2	\N	\N
2	4	\N	4	\N	\N
3	12	\N	10	\N	\N
4	2	\N	12	\N	\N
5	3	\N	\N	3	\N
6	2	48	\N	\N	\N
7	8	5	\N	\N	\N
8	5	\N	\N	\N	3
9	10	\N	\N	7	\N
10	9	\N	\N	7	\N
11	11	\N	\N	\N	4
12	6	\N	\N	\N	4
13	7	\N	\N	\N	5
14	4	3	\N	\N	\N
15	3	\N	\N	\N	6
16	7	\N	\N	5	\N
17	7	\N	\N	4	\N
18	5	\N	\N	6	\N
19	11	2	\N	\N	\N
20	3	4	\N	\N	\N
21	8	\N	\N	\N	9
22	10	\N	\N	\N	1
\.


--
-- Data for Name: articles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.articles (id, first_seen_scan_id, last_seen_scan_id, url, content_hash, title, content, language, published_at, effective_date, updated_at) FROM stdin;
1	1	1	https://example.com/news/2026/10/local-football-results	f0c0d9f47aae2c10f3e1a13b7f78e2efea9791fbbf6488fd01ec4731a3195631	Weekend football results roundup	A summary of weekend league matches and standings.	en	2026-10-17 18:00:00+00	\N	2026-10-27 13:04:51.101798+00
2	1	1	https://example.com/news/2026/10/red-sea-attacks-suez-diversions	fb129c61fc9c2e0afb9453870162a5044a5367bbbd081c8296d06d92c6d80a0b	Container lines divert vessels away from Suez Canal after renewed Red Sea attacks	Several major carriers announced that Asia–Europe services will be rerouted via the Cape of Good Hope, adding 10 to 14 days to transit times. Freight rates on the Shanghai–Mediterranean lane rose sharply.	en	2026-10-17 12:10:00+00	2026-10-19 21:00:00+00	2026-10-27 13:04:51.101798+00
3	1	1	https://example.com/haber/2026/10/cin-mensheli-guc-kaynaklarina-ilave-gumruk-vergisi	5a34daa39f32d363bff34ccf827efcb54841d8ccdcaa1d125fc9178f2e7c9cc5	Çin menşeli güç kaynaklarına ilave gümrük vergisi artırıldı	Resmî Gazete'de yayımlanan karar ile 8504.40 GTİP pozisyonundaki Çin menşeli güç kaynaklarına uygulanan ilave gümrük vergisi %11'den %20'ye çıkarıldı. Karar 1 Kasım 2026 itibarıyla yürürlüğe girecek.	tr	2026-10-17 20:30:00+00	2026-10-31 21:00:00+00	2026-10-27 13:04:51.101798+00
4	2	2	https://example.com/news/2026/10/kaohsiung-typhoon-port-closure	dcf44580c6f7593d1e6473d0004d8ba2492ac73042676cf3e3a394c53d2fc5ee	Typhoon forces temporary closure of Kaohsiung port	Port authorities suspended all berthing operations at Kaohsiung for at least three days as a strong typhoon approaches southern Taiwan. Backlogs are expected to persist into next week.	en	2026-10-18 15:20:00+00	2026-10-18 21:00:00+00	2026-10-27 13:04:51.101798+00
5	2	2	https://example.com/news/2026/10/dram-contract-prices-surge-q4	fa9304b69616eb23ef125905a0263982e98b4004a24c9788fdae0cd07190743c	DRAM contract prices expected to jump 15% in Q4 as AI demand tightens supply	Market analysts expect DDR5 contract prices to rise by roughly 15% quarter over quarter, as memory makers shift capacity to HBM for AI accelerators. Module makers including Kingston are expected to pass on the increase.	en	2026-10-18 07:45:00+00	2026-09-30 21:00:00+00	2026-10-27 13:04:51.101798+00
6	4	4	https://example.com/haber/2026/10/kultur-fonu-orani-degisikligi	ac4daac544f7fca4c4968b455e908a91c11e42c3f327de5100081e2a8145ab01	Bilgisayar depolama ürünlerinde kültür fonu kesintisi oranı yükseltildi	Cumhurbaşkanı kararı ile 8471.70 pozisyonundaki depolama birimlerine uygulanan kültür fonu oranı %1'den %2'ye çıkarıldı.	tr	2026-10-20 08:15:00+00	2026-11-14 21:00:00+00	2026-10-27 13:04:51.101798+00
7	4	4	https://example.com/news/2026/10/nvidia-rtx-5060-supply-shortage	e60094d44129f13274ba4000bfc10fedc030d5636eb8d04732fe65565e908e72	Graphics card shortage: RTX 5060 board partners report constrained GPU allocation	Board partners such as ASUS and Gigabyte report reduced GPU allocations for the RTX 5060 series, with retail prices climbing 8–12% in several markets.	en	2026-10-20 06:00:00+00	2026-10-19 21:00:00+00	2026-10-27 13:04:51.101798+00
8	5	5	https://example.com/news/2026/10/vietnam-export-controls-electronics	df065946a29105d5cf2ae9a3bd88b7fa96c0c89f7cbbb006b37fe4f839b475f4	Vietnam tightens export documentation rules for electronics	New certificate-of-origin verification requirements for electronics exports from Vietnam take effect next month, potentially slowing customs clearance for monitors and components.	en	2026-10-20 10:00:00+00	2026-11-09 21:00:00+00	2026-10-27 13:04:51.101798+00
9	5	5	https://example.com/news/2026/10/malaysia-penang-airport-strike	49c182905cf1ae36651d53610f2dd4f035034835c341bee648a7952c5a8959ec	Ground handling strike disrupts cargo flights at Penang airport	A 48-hour strike by ground handling staff at Penang International Airport has delayed outbound cargo, including semiconductor shipments from local assembly plants.	en	2026-10-20 17:40:00+00	2026-10-20 21:00:00+00	2026-10-27 13:04:51.101798+00
10	6	6	https://example.com/news/2026/10/intel-core-ultra-price-cut	b3332321a185a1e1c22bb816f7e124a2e52d53a03e6ae99df641fd62463b47f2	Intel trims prices of Core Ultra 200S desktop CPUs	Intel reduced list prices for several Core Ultra 200S processors by around 5% ahead of the holiday season.	en	2026-10-21 16:00:00+00	2026-10-24 21:00:00+00	2026-10-27 13:04:51.101798+00
11	6	6	https://example.com/news/2026/10/korea-turkey-fta-ssd-tariff	5fee71ba66e1723476b3583d593b454f5eb3ba0680b4c65c36c578bd23c8f287	South Korea and Türkiye agree to cut tariffs on additional IT products	An amendment to the Korea–Türkiye FTA removes remaining duties on a number of IT products, including solid-state drives, starting January 2027.	en	2026-10-21 05:00:00+00	2026-12-31 21:00:00+00	2026-10-27 13:04:51.101798+00
12	6	6	https://example.com/haber/2026/10/mersin-limani-yogunluk	3d6eed0c98d60219bfc6d81fe4566b1e5bc01ae883670f55d8868467c68607a4	Mersin Limanı'nda konteyner yoğunluğu: bekleme süreleri uzadı	Mersin Limanı'nda artan ithalat hacmi ve vinç arızası nedeniyle gemi bekleme süreleri ortalama 4 güne çıktı.	tr	2026-10-21 14:30:00+00	2026-10-21 21:00:00+00	2026-10-27 13:04:51.101798+00
\.


--
-- Data for Name: contracts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contracts (id, supplier_item_id, start_date, end_date, currency, purchase_amount, unit_price, contract_date, is_active, created_at, updated_at) FROM stdin;
1	1	2026-10-01	2026-12-31	USD	\N	208.1500	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
2	2	2026-01-01	2026-12-31	USD	\N	59.9500	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
3	3	2026-10-01	2026-12-31	USD	\N	635.0000	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
4	4	2026-01-01	2026-12-31	USD	\N	119.9900	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
5	5	2026-01-01	2026-12-31	USD	\N	99.0000	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
6	6	2026-10-01	2026-12-31	USD	\N	469.9900	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
7	7	2026-01-01	2026-12-31	USD	\N	159.9900	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
8	8	2026-10-01	2026-12-31	USD	\N	179.5900	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
9	9	2026-01-01	2026-12-31	USD	\N	159.9900	\N	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
\.


--
-- Data for Name: countries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.countries (id, iso_code, name_tr, name_en, has_trade_agreement) FROM stdin;
1	MYS	Malezya	Malaysia	t
2	KOR	Güney Kore	South Korea	t
3	TWN	Tayvan	Taiwan	f
4	CHN	Çin	China	f
5	VNM	Vietnam	Vietnam	f
6	TUR	Türkiye	Türkiye	f
7	JPN	Japonya	Japan	f
8	THA	Tayland	Thailand	f
9	IDN	Endonezya	Indonesia	f
10	PHL	Filipinler	Philippines	f
11	IND	Hindistan	India	f
12	SGP	Singapur	Singapore	t
13	HKG	Hong Kong	Hong Kong	f
14	BGD	Bangladeş	Bangladesh	f
15	KHM	Kamboçya	Cambodia	f
16	AUS	Avustralya	Australia	f
17	USA	Amerika Birleşik Devletleri	United States	f
18	CAN	Kanada	Canada	f
19	MEX	Meksika	Mexico	f
20	BRA	Brezilya	Brazil	f
21	CHL	Şili	Chile	t
22	DEU	Almanya	Germany	t
23	NLD	Hollanda	Netherlands	t
24	FRA	Fransa	France	t
25	ITA	İtalya	Italy	t
26	ESP	İspanya	Spain	t
27	POL	Polonya	Poland	t
28	CZE	Çekya	Czechia	t
29	HUN	Macaristan	Hungary	t
30	ROU	Romanya	Romania	t
31	IRL	İrlanda	Ireland	t
32	SWE	İsveç	Sweden	t
33	AUT	Avusturya	Austria	t
34	GBR	Birleşik Krallık	United Kingdom	t
35	CHE	İsviçre	Switzerland	t
36	NOR	Norveç	Norway	t
37	UKR	Ukrayna	Ukraine	t
38	MDA	Moldova	Moldova	t
39	SRB	Sırbistan	Serbia	t
40	MKD	Kuzey Makedonya	North Macedonia	t
41	BIH	Bosna-Hersek	Bosnia and Herzegovina	t
42	ALB	Arnavutluk	Albania	t
43	GEO	Gürcistan	Georgia	t
44	AZE	Azerbaycan	Azerbaijan	f
45	ARE	Birleşik Arap Emirlikleri	United Arab Emirates	t
46	QAT	Katar	Qatar	t
47	SAU	Suudi Arabistan	Saudi Arabia	f
48	EGY	Mısır	Egypt	t
49	MAR	Fas	Morocco	t
50	TUN	Tunus	Tunisia	t
\.


--
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory (id, supplier_item_id, on_hand, reserved, reorder_point, updated_at) FROM stdin;
1	9	1014.000	192.000	438.000	2026-10-27 13:04:51.037595+00
2	7	1699.000	192.000	1096.000	2026-10-27 13:04:51.037595+00
3	3	466.000	192.000	438.000	2026-10-27 13:04:51.037595+00
4	1	877.000	192.000	438.000	2026-10-27 13:04:51.037595+00
5	6	370.000	96.000	521.000	2026-10-27 13:04:51.037595+00
6	5	1151.000	192.000	1041.000	2026-10-27 13:04:51.037595+00
7	4	1562.000	192.000	1068.000	2026-10-27 13:04:51.037595+00
8	2	1014.000	192.000	1041.000	2026-10-27 13:04:51.037595+00
9	8	712.000	96.000	479.000	2026-10-27 13:04:51.037595+00
\.


--
-- Data for Name: items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.items (id, name, hs6, gtip, unit, kdv_rate, otv_rate, kultur_fonu_rate, source_id, checked_at) FROM stdin;
1	İşlemci	854231	854231900000	adet	20.00	0.0000	0.00	1	\N
2	Anakart	847330	847330200000	adet	20.00	0.0000	0.00	1	\N
3	Bellek	847330	847330200000	adet	20.00	0.0000	0.00	1	\N
4	SSD	847170	847170989000	adet	20.00	0.0000	1.00	1	\N
5	Ekran kartı	847330	847330200000	adet	20.00	0.0000	0.00	1	\N
6	Güç kaynağı	850440	850440839019	adet	20.00	0.0000	0.00	1	\N
7	Kasa	847330	847330800000	adet	20.00	0.0000	0.00	1	\N
8	Soğutucu	841459	841459150000	adet	20.00	0.0000	0.00	1	\N
9	Monitör	852852	852852100000	adet	20.00	0.0000	0.00	1	\N
\.


--
-- Data for Name: locations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.locations (id, name, code, location_type, country_id) FROM stdin;
1	Tan Son Nhat Uluslararası Havalimanı	SGN	airport	5
2	Penang Uluslararası Havalimanı	PEN	airport	1
3	Incheon Uluslararası Havalimanı	ICN	airport	2
4	Kaohsiung Limanı	TWKHH	port	3
5	Taoyuan Uluslararası Havalimanı	TPE	airport	3
6	Yantian Limanı (Shenzhen)	CNYTN	port	4
7	Shekou Limanı (Shenzhen)	CNSHK	port	4
8	Ningbo-Zhoushan Limanı	CNNBG	port	4
9	Cai Mep Limanı	VNTOT	port	5
10	Mersin Limanı	TRMER	port	6
11	İstanbul Havalimanı	IST	airport	6
12	Süveyş Kanalı	\N	chokepoint	\N
\.


--
-- Data for Name: rate_sources; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rate_sources (id, name, url) FROM stdin;
1	TARA (Ticaret Bakanlığı)	https://ticaret.gov.tr
\.


--
-- Data for Name: scan_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scan_logs (id, triggered_by, status, started_at, finished_at, error_message) FROM stdin;
1	schedule	success	2026-10-18 03:00:00+00	2026-10-18 03:04:12+00	\N
2	schedule	success	2026-10-19 03:00:00+00	2026-10-19 03:03:47+00	\N
3	schedule	failed	2026-10-20 03:00:00+00	2026-10-20 03:00:31+00	Haber kaynağına bağlanılamadı: timeout (30s)
4	manual	success	2026-10-20 11:25:00+00	2026-10-20 11:29:05+00	\N
5	schedule	success	2026-10-21 03:00:00+00	2026-10-21 03:05:20+00	\N
6	schedule	success	2026-10-22 03:00:00+00	2026-10-22 03:04:02+00	\N
7	schedule	running	2026-10-23 03:00:00+00	\N	\N
\.


--
-- Data for Name: shipments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shipments (id, contract_id, transport_mode, origin_country_id, exit_location_id, destination_location_id, status, expected_transit_days) FROM stdin;
1	1	air	2	3	11	planned	1
2	2	sea	3	4	10	planned	23
3	3	air	3	5	11	planned	1
4	4	sea	4	6	10	planned	24
5	5	sea	4	7	10	planned	23
6	6	sea	4	7	10	planned	23
7	7	sea	4	8	10	planned	25
8	8	sea	5	9	10	planned	20
9	9	air	5	1	11	planned	1
\.


--
-- Data for Name: supplier_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.supplier_items (id, supplier_id, item_id, item_model, assembly_country_id) FROM stdin;
1	1	4	Samsung 990 EVO Plus 1 TB (MZ-V9S1T0BW)	2
2	8	8	Noctua NH-U12S redux	3
3	6	3	Kingston FURY Beast 32 GB (2x16) DDR5-6000 (KF560C30BBEK2-32)	3
4	2	7	Cooler Master MasterBox TD500 Mesh V2	4
5	3	6	FSP VITA GM 650 W (ATX 3.1, 80+ Gold)	4
6	4	5	ASUS Dual GeForce RTX 5060 OC 8 GB (DUAL-RTX5060-O8G)	4
7	5	2	Gigabyte B860 Gaming X WiFi6E (ATX)	4
8	1	9	Samsung Odyssey G3 24 inç (LS24DG302ENXZA)	5
9	7	1	Intel Core Ultra 5 225 (BX80768225)	5
\.


--
-- Data for Name: suppliers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.suppliers (id, name, name_original, country_id, is_active, created_at, updated_at) FROM stdin;
1	Samsung	Samsung Electronics Co., Ltd.	2	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
2	Cooler Master	Cooler Master Technology Inc.	3	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
3	FSP	FSP Technology Inc.	3	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
4	ASUS	ASUSTeK Computer Inc.	3	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
5	Gigabyte	GIGA-BYTE Technology Co., Ltd.	3	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
6	Kingston	Kingston Technology Company, Inc.	17	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
7	Intel	Intel Corporation	17	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
8	Noctua	Rascom Computerdistribution Ges.m.b.H.	33	t	2026-10-27 13:04:51.037595+00	2026-10-27 13:04:51.037595+00
\.


--
-- Data for Name: tariffs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tariffs (id, item_id, country_id, gv_rate, igv_rate, valid_from, valid_to, source_id, checked_at) FROM stdin;
1	1	5	0.00	0.00	2026-01-01	\N	1	\N
2	2	4	0.00	0.00	2026-01-01	\N	1	\N
3	3	3	0.00	0.00	2026-01-01	\N	1	\N
4	4	2	0.00	0.00	2026-01-01	\N	1	\N
5	5	4	0.00	0.00	2026-01-01	\N	1	\N
6	6	4	3.30	11.00	2026-01-01	\N	1	\N
7	7	4	0.00	0.00	2026-01-01	\N	1	\N
8	8	3	2.30	0.00	2026-01-01	\N	1	\N
9	9	5	0.00	0.00	2026-01-01	\N	1	\N
\.


--
-- Name: alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alerts_id_seq', 1, false);


--
-- Name: article_analyses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.article_analyses_id_seq', 12, true);


--
-- Name: article_impacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.article_impacts_id_seq', 22, true);


--
-- Name: articles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.articles_id_seq', 12, true);


--
-- Name: contracts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contracts_id_seq', 9, true);


--
-- Name: countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.countries_id_seq', 51, false);


--
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_id_seq', 9, true);


--
-- Name: items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.items_id_seq', 10, false);


--
-- Name: locations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.locations_id_seq', 13, false);


--
-- Name: rate_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rate_sources_id_seq', 2, false);


--
-- Name: scan_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scan_logs_id_seq', 7, true);


--
-- Name: shipments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.shipments_id_seq', 9, true);


--
-- Name: supplier_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.supplier_items_id_seq', 9, true);


--
-- Name: suppliers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.suppliers_id_seq', 8, true);


--
-- Name: tariffs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tariffs_id_seq', 10, false);


--
-- Name: alert_articles alert_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_articles
    ADD CONSTRAINT alert_articles_pkey PRIMARY KEY (alert_id, article_id);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (id);


--
-- Name: article_analyses article_analyses_article_id_scan_log_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses
    ADD CONSTRAINT article_analyses_article_id_scan_log_id_key UNIQUE (article_id, scan_log_id);


--
-- Name: article_analyses article_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses
    ADD CONSTRAINT article_analyses_pkey PRIMARY KEY (id);


--
-- Name: article_impacts article_impacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts
    ADD CONSTRAINT article_impacts_pkey PRIMARY KEY (id);


--
-- Name: articles articles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_pkey PRIMARY KEY (id);


--
-- Name: articles articles_url_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_url_key UNIQUE (url);


--
-- Name: contracts contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_pkey PRIMARY KEY (id);


--
-- Name: countries countries_iso_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_iso_code_key UNIQUE (iso_code);


--
-- Name: countries countries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_pkey PRIMARY KEY (id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- Name: inventory inventory_supplier_item_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_supplier_item_id_key UNIQUE (supplier_item_id);


--
-- Name: items items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_pkey PRIMARY KEY (id);


--
-- Name: locations locations_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_code_key UNIQUE (code);


--
-- Name: locations locations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_pkey PRIMARY KEY (id);


--
-- Name: rate_sources rate_sources_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rate_sources
    ADD CONSTRAINT rate_sources_name_key UNIQUE (name);


--
-- Name: rate_sources rate_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rate_sources
    ADD CONSTRAINT rate_sources_pkey PRIMARY KEY (id);


--
-- Name: scan_logs scan_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scan_logs
    ADD CONSTRAINT scan_logs_pkey PRIMARY KEY (id);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (id);


--
-- Name: supplier_items supplier_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_items
    ADD CONSTRAINT supplier_items_pkey PRIMARY KEY (id);


--
-- Name: supplier_items supplier_items_supplier_id_item_id_item_model_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_items
    ADD CONSTRAINT supplier_items_supplier_id_item_id_item_model_key UNIQUE (supplier_id, item_id, item_model);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: tariffs tariffs_item_id_country_id_valid_from_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_item_id_country_id_valid_from_key UNIQUE (item_id, country_id, valid_from);


--
-- Name: tariffs tariffs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_pkey PRIMARY KEY (id);


--
-- Name: idx_alert_articles_article; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_articles_article ON public.alert_articles USING btree (article_id);


--
-- Name: idx_alerts_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_location ON public.alerts USING btree (location_id);


--
-- Name: idx_alerts_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_priority ON public.alerts USING btree (priority_score DESC) WHERE ((status)::text <> 'resolved'::text);


--
-- Name: idx_alerts_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_status ON public.alerts USING btree (status);


--
-- Name: idx_alerts_supplier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerts_supplier ON public.alerts USING btree (supplier_id);


--
-- Name: idx_analyses_scan; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analyses_scan ON public.article_analyses USING btree (scan_log_id);


--
-- Name: idx_articles_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_hash ON public.articles USING btree (content_hash);


--
-- Name: idx_articles_last_seen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_last_seen ON public.articles USING btree (last_seen_scan_id);


--
-- Name: idx_articles_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_articles_published ON public.articles USING btree (published_at);


--
-- Name: idx_contracts_supplier_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contracts_supplier_item ON public.contracts USING btree (supplier_item_id);


--
-- Name: idx_impacts_analysis; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_impacts_analysis ON public.article_impacts USING btree (article_analysis_id);


--
-- Name: idx_impacts_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_impacts_country ON public.article_impacts USING btree (country_id);


--
-- Name: idx_impacts_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_impacts_item ON public.article_impacts USING btree (item_id);


--
-- Name: idx_impacts_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_impacts_location ON public.article_impacts USING btree (location_id);


--
-- Name: idx_impacts_supplier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_impacts_supplier ON public.article_impacts USING btree (supplier_id);


--
-- Name: idx_items_hs6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_items_hs6 ON public.items USING btree (hs6);


--
-- Name: idx_shipments_contract; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shipments_contract ON public.shipments USING btree (contract_id);


--
-- Name: idx_shipments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shipments_status ON public.shipments USING btree (status);


--
-- Name: idx_supplier_items_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_supplier_items_item ON public.supplier_items USING btree (item_id);


--
-- Name: idx_suppliers_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_suppliers_country ON public.suppliers USING btree (country_id);


--
-- Name: uq_alerts_open_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_alerts_open_risk ON public.alerts USING btree (risk_key) WHERE ((status)::text <> 'resolved'::text);


--
-- Name: alert_articles alert_articles_added_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_articles
    ADD CONSTRAINT alert_articles_added_scan_id_fkey FOREIGN KEY (added_scan_id) REFERENCES public.scan_logs(id);


--
-- Name: alert_articles alert_articles_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_articles
    ADD CONSTRAINT alert_articles_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(id) ON DELETE CASCADE;


--
-- Name: alert_articles alert_articles_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_articles
    ADD CONSTRAINT alert_articles_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: alerts alerts_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: alerts alerts_first_seen_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_first_seen_scan_id_fkey FOREIGN KEY (first_seen_scan_id) REFERENCES public.scan_logs(id);


--
-- Name: alerts alerts_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: alerts alerts_last_seen_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_last_seen_scan_id_fkey FOREIGN KEY (last_seen_scan_id) REFERENCES public.scan_logs(id);


--
-- Name: alerts alerts_latest_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_latest_analysis_id_fkey FOREIGN KEY (latest_analysis_id) REFERENCES public.article_analyses(id) ON DELETE SET NULL;


--
-- Name: alerts alerts_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id);


--
-- Name: alerts alerts_resolved_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_resolved_scan_id_fkey FOREIGN KEY (resolved_scan_id) REFERENCES public.scan_logs(id);


--
-- Name: alerts alerts_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: article_analyses article_analyses_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses
    ADD CONSTRAINT article_analyses_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_analyses article_analyses_scan_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses
    ADD CONSTRAINT article_analyses_scan_log_id_fkey FOREIGN KEY (scan_log_id) REFERENCES public.scan_logs(id) ON DELETE CASCADE;


--
-- Name: article_impacts article_impacts_article_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts
    ADD CONSTRAINT article_impacts_article_analysis_id_fkey FOREIGN KEY (article_analysis_id) REFERENCES public.article_analyses(id) ON DELETE CASCADE;


--
-- Name: article_impacts article_impacts_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts
    ADD CONSTRAINT article_impacts_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: article_impacts article_impacts_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts
    ADD CONSTRAINT article_impacts_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: article_impacts article_impacts_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts
    ADD CONSTRAINT article_impacts_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.locations(id);


--
-- Name: article_impacts article_impacts_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_impacts
    ADD CONSTRAINT article_impacts_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: articles articles_first_seen_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_first_seen_scan_id_fkey FOREIGN KEY (first_seen_scan_id) REFERENCES public.scan_logs(id);


--
-- Name: articles articles_last_seen_scan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_last_seen_scan_id_fkey FOREIGN KEY (last_seen_scan_id) REFERENCES public.scan_logs(id);


--
-- Name: contracts contracts_supplier_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_supplier_item_id_fkey FOREIGN KEY (supplier_item_id) REFERENCES public.supplier_items(id);


--
-- Name: inventory inventory_supplier_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_supplier_item_id_fkey FOREIGN KEY (supplier_item_id) REFERENCES public.supplier_items(id);


--
-- Name: items items_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.rate_sources(id);


--
-- Name: locations locations_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.locations
    ADD CONSTRAINT locations_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: shipments shipments_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id);


--
-- Name: shipments shipments_destination_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_destination_location_id_fkey FOREIGN KEY (destination_location_id) REFERENCES public.locations(id);


--
-- Name: shipments shipments_exit_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_exit_location_id_fkey FOREIGN KEY (exit_location_id) REFERENCES public.locations(id);


--
-- Name: shipments shipments_origin_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_origin_country_id_fkey FOREIGN KEY (origin_country_id) REFERENCES public.countries(id);


--
-- Name: supplier_items supplier_items_assembly_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_items
    ADD CONSTRAINT supplier_items_assembly_country_id_fkey FOREIGN KEY (assembly_country_id) REFERENCES public.countries(id);


--
-- Name: supplier_items supplier_items_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_items
    ADD CONSTRAINT supplier_items_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: supplier_items supplier_items_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_items
    ADD CONSTRAINT supplier_items_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE CASCADE;


--
-- Name: suppliers suppliers_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: tariffs tariffs_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- Name: tariffs tariffs_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id) ON DELETE CASCADE;


--
-- Name: tariffs tariffs_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tariffs
    ADD CONSTRAINT tariffs_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.rate_sources(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Ejyfbilplc7JJGm238TOWObfsMefHKP2ArrPQHmK2tWhXPb4R7BCcwYTgQGqu0z

