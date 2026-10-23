--
-- PostgreSQL database dump
--

\restrict q4a5uIZOeUruCH6AHTNqwAMIdCQHUgQSWNdLlpuTsspLvSSIdbGbn2HPGXGAG5j

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

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: article_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.article_analyses (
    id integer NOT NULL,
    article_id integer NOT NULL,
    is_relevant boolean NOT NULL,
    impact_score smallint,
    event_type character varying(30),
    summary text,
    rate_type character varying(20),
    old_rate_pct numeric(6,2),
    new_rate_pct numeric(6,2),
    expected_delay_days integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT article_analyses_event_type_check CHECK (((event_type)::text = ANY (ARRAY[('tariff_increase'::character varying)::text, ('tariff_decrease'::character varying)::text, ('trade_restriction'::character varying)::text, ('transport_disruption'::character varying)::text, ('price_change'::character varying)::text, ('not_relevant'::character varying)::text, ('other'::character varying)::text]))),
    CONSTRAINT article_analyses_expected_delay_days_check CHECK ((expected_delay_days >= 0)),
    CONSTRAINT article_analyses_impact_score_check CHECK (((impact_score >= 1) AND (impact_score <= 100))),
    CONSTRAINT article_analyses_rate_type_check CHECK (((rate_type)::text = ANY (ARRAY[('gv'::character varying)::text, ('igv'::character varying)::text, ('kultur_fonu'::character varying)::text, ('kdv'::character varying)::text, ('otv'::character varying)::text])))
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
    scan_log_id integer NOT NULL,
    url text NOT NULL,
    title text NOT NULL,
    content text,
    language character(2),
    published_at timestamp with time zone,
    affective_date timestamp with time zone
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
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    price_date date,
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
    CONSTRAINT locations_location_type_check CHECK (((location_type)::text = ANY (ARRAY[('port'::character varying)::text, ('airport'::character varying)::text, ('border_gate'::character varying)::text, ('chokepoint'::character varying)::text])))
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
    CONSTRAINT scan_logs_status_check CHECK (((status)::text = ANY (ARRAY[('running'::character varying)::text, ('success'::character varying)::text, ('failed'::character varying)::text]))),
    CONSTRAINT scan_logs_triggered_by_check CHECK (((triggered_by)::text = ANY (ARRAY[('schedule'::character varying)::text, ('manual'::character varying)::text])))
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
    chokepoint_location_id integer,
    status character varying(15) DEFAULT 'planned'::character varying NOT NULL,
    expected_transit_days integer,
    CONSTRAINT shipments_status_check CHECK (((status)::text = ANY (ARRAY[('planned'::character varying)::text, ('in_transit'::character varying)::text, ('delayed'::character varying)::text, ('arrived'::character varying)::text, ('cancelled'::character varying)::text]))),
    CONSTRAINT shipments_transport_mode_check CHECK (((transport_mode)::text = ANY (ARRAY[('sea'::character varying)::text, ('air'::character varying)::text, ('road'::character varying)::text])))
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
-- Data for Name: article_analyses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.article_analyses (id, article_id, is_relevant, impact_score, event_type, summary, rate_type, old_rate_pct, new_rate_pct, expected_delay_days, created_at) FROM stdin;
\.


--
-- Data for Name: article_impacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.article_impacts (id, article_analysis_id, country_id, location_id, supplier_id, item_id) FROM stdin;
\.


--
-- Data for Name: articles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.articles (id, scan_log_id, url, title, content, language, published_at, affective_date) FROM stdin;
\.


--
-- Data for Name: contracts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contracts (id, supplier_item_id, start_date, end_date, currency, purchase_amount, unit_price, is_active, created_at, updated_at, price_date) FROM stdin;
1	1	2026-10-01	2026-12-31	USD	16652.000	208.1500	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
2	2	2026-01-01	2026-12-31	USD	109135.000	59.9500	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
3	3	2026-10-01	2026-12-31	USD	18400.000	635.0000	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
4	4	2026-01-01	2026-12-31	USD	86140.000	119.9900	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
6	6	2026-10-01	2026-12-31	USD	13800.000	469.9900	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
7	7	2026-01-01	2026-12-31	USD	67525.000	159.9900	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
9	9	2026-01-01	2026-12-31	USD	65700.000	159.9900	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-21
5	5	2026-01-01	2026-12-31	USD	78475.000	99.0000	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2024-04-11
8	8	2026-10-01	2026-12-31	USD	17572.000	179.5900	t	2026-10-22 13:05:49.14683+00	2026-10-22 14:16:12.845907+00	2026-10-13
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
1	9	1562.000	180.000	1260.000	2026-10-22 13:07:23.77726+00
2	7	1682.000	185.000	1295.000	2026-10-22 13:07:23.77726+00
3	3	1700.000	200.000	1400.000	2026-10-22 13:07:23.77726+00
4	1	1369.000	181.000	1267.000	2026-10-22 13:07:23.77726+00
5	6	1305.000	150.000	1050.000	2026-10-22 13:07:23.77726+00
6	5	1897.000	215.000	1505.000	2026-10-22 13:07:23.77726+00
7	4	2000.000	236.000	1652.000	2026-10-22 13:07:23.77726+00
8	2	1573.000	299.000	2093.000	2026-10-22 13:07:23.77726+00
9	8	1999.000	191.000	1337.000	2026-10-22 13:07:23.77726+00
\.


--
-- Data for Name: items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.items (id, name, hs6, gtip, unit, kdv_rate, otv_rate, kultur_fonu_rate, source_id, checked_at) FROM stdin;
1	İşlemci	854231	854231900000	adet	20.00	0.0000	0.00	1	2026-10-21
2	Anakart	847330	847330200000	adet	20.00	0.0000	0.00	1	2026-10-21
3	Bellek	847330	847330200000	adet	20.00	0.0000	0.00	1	2026-10-21
4	SSD	847170	847170989000	adet	20.00	0.0000	1.00	1	2026-10-21
5	Ekran kartı	847330	847330200000	adet	20.00	0.0000	0.00	1	2026-10-21
6	Güç kaynağı	850440	850440839019	adet	20.00	0.0000	0.00	1	2026-10-21
7	Kasa	847330	847330800000	adet	20.00	0.0000	0.00	1	2026-10-21
8	Soğutucu	841459	841459150000	adet	20.00	0.0000	0.00	1	2026-10-21
9	Monitör	852852	852852100000	adet	20.00	0.0000	0.00	1	2026-10-21
\.


--
-- Data for Name: locations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.locations (id, name, code, location_type, country_id) FROM stdin;
1	Kuala Lumpur Uluslararası Havalimanı	KUL	airport	1
2	Penang Uluslararası Havalimanı	PEN	airport	1
3	Incheon Uluslararası Havalimanı	ICN	airport	2
4	Kaohsiung Limanı	TWKHH	port	3
5	Taoyuan Uluslararası Havalimanı	TPE	airport	3
6	Yantian Limanı (Shenzhen)	CNYTN	port	4
7	Shekou Limanı (Shenzhen)	CNSHK	port	4
8	Ningbo Limanı	CNNBG	port	4
10	Mersin Limanı	TRMER	port	6
11	İstanbul Havalimanı	IST	airport	6
12	Süveyş Kanalı	\N	chokepoint	\N
9	Port of Cai Mep	VNTOT	port	5
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
\.


--
-- Data for Name: shipments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shipments (id, contract_id, transport_mode, origin_country_id, exit_location_id, destination_location_id, chokepoint_location_id, status, expected_transit_days) FROM stdin;
1	1	air	2	3	11	\N	planned	1
2	2	sea	3	4	10	12	planned	23
3	3	air	3	5	11	\N	planned	1
4	4	sea	4	6	10	12	planned	24
5	5	sea	4	7	10	12	planned	23
6	6	sea	4	7	10	12	planned	23
7	7	sea	4	8	10	12	planned	25
8	8	sea	5	9	10	12	planned	20
9	9	air	1	2	11	\N	planned	1
10	1	air	2	3	11	\N	planned	1
11	2	sea	3	4	10	12	planned	23
12	3	air	3	5	11	\N	planned	1
13	4	sea	4	6	10	12	planned	24
14	5	sea	4	7	10	12	planned	23
15	6	sea	4	7	10	12	planned	23
16	7	sea	4	8	10	12	planned	25
17	8	sea	5	9	10	12	planned	20
18	9	air	1	2	11	\N	planned	1
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
1	Samsung	Samsung Electronics Co., Ltd.	2	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
2	Cooler Master	Cooler Master Technology Inc.	3	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
3	FSP	FSP Technology Inc.	3	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
4	ASUS	ASUSTeK Computer Inc.	3	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
5	Gigabyte	GIGA-BYTE Technology Co., Ltd.	3	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
6	Kingston	Kingston Technology Company, Inc.	17	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
7	Intel	Intel Corporation	17	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
8	Noctua	Rascom Computerdistribution Ges.m.b.H.	33	t	2026-10-22 12:42:36.204497+00	2026-10-22 12:42:36.204497+00
\.


--
-- Data for Name: tariffs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tariffs (id, item_id, country_id, gv_rate, igv_rate, valid_from, valid_to, source_id, checked_at) FROM stdin;
1	1	1	0.00	0.00	2026-01-01	\N	1	2026-10-21
2	4	2	0.00	0.00	2026-01-01	\N	1	2026-10-21
3	8	3	2.30	0.00	2026-01-01	\N	1	2026-10-21
4	3	3	0.00	0.00	2026-01-01	\N	1	2026-10-21
5	7	4	0.00	0.00	2026-01-01	\N	1	2026-10-21
6	6	4	3.30	11.00	2026-01-01	\N	1	2026-10-21
7	5	4	0.00	0.00	2026-01-01	\N	1	2026-10-21
8	2	4	0.00	0.00	2026-01-01	\N	1	2026-10-21
9	9	5	0.00	0.00	2026-01-01	\N	1	2026-10-21
\.


--
-- Name: article_analyses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.article_analyses_id_seq', 1, false);


--
-- Name: article_impacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.article_impacts_id_seq', 1, false);


--
-- Name: articles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.articles_id_seq', 1, false);


--
-- Name: contracts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contracts_id_seq', 9, true);


--
-- Name: countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.countries_id_seq', 50, true);


--
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_id_seq', 9, true);


--
-- Name: items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.items_id_seq', 9, true);


--
-- Name: locations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.locations_id_seq', 13, true);


--
-- Name: rate_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rate_sources_id_seq', 1, true);


--
-- Name: scan_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scan_logs_id_seq', 1, false);


--
-- Name: shipments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.shipments_id_seq', 18, true);


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

SELECT pg_catalog.setval('public.tariffs_id_seq', 9, true);


--
-- Name: article_analyses article_analyses_article_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses
    ADD CONSTRAINT article_analyses_article_id_key UNIQUE (article_id);


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
-- Name: article_analyses article_analyses_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.article_analyses
    ADD CONSTRAINT article_analyses_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


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
-- Name: articles articles_scan_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_scan_log_id_fkey FOREIGN KEY (scan_log_id) REFERENCES public.scan_logs(id);


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
-- Name: shipments shipments_chokepoint_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_chokepoint_location_id_fkey FOREIGN KEY (chokepoint_location_id) REFERENCES public.locations(id);


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

\unrestrict q4a5uIZOeUruCH6AHTNqwAMIdCQHUgQSWNdLlpuTsspLvSSIdbGbn2HPGXGAG5j

