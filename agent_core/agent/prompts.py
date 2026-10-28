"""Prompts for the screening filter and the impact analysis.

Both stages share one context (COMMON_CONTEXT) that defines what counts as relevant:
Turkish duties and taxes on the product, trade restrictions, disruptions at the
supplier's own ports and airports, concrete price changes and supplier-specific
changes. Articles can be in any language; answers are always in English.
The supplier list comes from data/suppliers.json, so the prompts do not change when
the company or its suppliers change.
"""

import json

DEFAULT_COMPANY = "a manufacturer based in Turkey"

COMMON_CONTEXT = """You work for the procurement risk system of {company}.
The company buys the components listed below from foreign suppliers and IMPORTS them into Turkey.

Each supplier record describes what we buy and how it reaches us: name (brand) and part_en (what we buy),
hs6 (customs code), origin_country (customs origin; Turkish duties follow it), assembly_countries
(where it is assembled, if different from the origin), trade_agreement_with_turkey, transport_mode,
departure_point (export port or airport) and arrival_point (where it enters Turkey).

Classify every news item as 'direct' (RELEVANT) or 'none' (NOT relevant).

DIRECT - the news can change the cost, availability or delivery time of what WE buy from a specific
supplier. ONLY these cases (draft or proposed measures count too; the analysis records them as proposed):
  1) TARIFFS AND TAXES - customs duties or additional customs duties applied BY TURKEY on imports of the
     product from the supplier's origin_country, or a change in a trade agreement between Turkey and that
     country that changes duties. Also changes of other Turkish taxes on the product (VAT / KDV, special
     consumption tax / OTV, Culture Fund / Kultur Fonu): these apply whatever the origin country.
     A tariff applies ONLY to the products it names: if the text gives an HS code, compare it with the
     first digits of the supplier's hs6 (a duty on HS 1234.56 covers a supplier with hs6 1234.56 but not
     one with 1234.99 or 6543.21); otherwise match the product description. A tariff also applies only to
     the countries it names. NEVER extend a tariff to other products or other countries.
  2) TRADE RESTRICTIONS - bans, quotas, licence requirements, sanctions, or new mandatory certificates or
     conformity documents without which the product cannot clear customs, that stop or limit the product
     leaving the supplier's origin_country or one of its assembly_countries, or entering Turkey.
  3) TRANSPORT DISRUPTIONS - strikes, disasters, accidents, congestion or closures at a supplier's
     departure_point or arrival_point. A point counts when the text names it or the city
     it serves (e.g. "the ports of a city" covers every port of that city in the list). The city name
     alone is not enough: the problem must be at the same kind of point the supplier uses (see its
     transport_mode). A problem at a city's airport does not affect its seaport, and vice versa.
     An arrival point in Turkey is shared: a disruption there is DIRECT for EVERY supplier whose
     arrival_point it is. Do not assume a problem at one port hits other ports of the same country, but if
     the text says that ALL sea or air shipments from a whole country are halted, it is DIRECT for every
     supplier whose departure_point is in that country and uses that transport mode.
  4) PRICES - a CONCRETE, sharp market price change of a part we buy, stated in the text as a figure or as
     a clear rise or fall of that product's price (e.g. "DDR5 memory module prices up 40 percent this
     quarter"). A FORECAST of such a change counts too when it gives a figure for the part we buy (e.g.
     "DDR5 contract prices are expected to rise 15% next quarter"); the analysis records it as unclear.
     Opinions, criticism or commentary about prices, and general remarks such as "prices are high" or
     "rising costs" without a concrete figure for the part we buy, are NOT enough.
  5) OTHER - the supplier stops making or recalls the kind of part we buy from it. The data has no model
     numbers: judge by the brand and the part type, and if the text names a specific model, treat it as
     ours only when the part type and brand match.

NONE - everything else, including:
  - fires, strikes, disasters or shutdowns at FACTORIES or production plants, and general disasters in a
    country, unless the text says a departure or arrival point or its shipments are disrupted
  - measures between OTHER countries that do not involve Turkey as the importer (e.g. tariffs one foreign
    country puts on another), and EU measures unless the text says Turkey applies them
  - general global shipping delays, freight-rate trends and problems on sea routes between the points,
    including closures of or diversions around canals and straits (e.g. the Suez Canal or the Red Sea):
    only the departure_point and arrival_point in the list count; never assume which route a shipment takes
  - routine company news (new products, earnings, investments) that does not change supply or price
  - opinions, interviews or commentary about prices, and price news about other products (e.g. phone
    memory chips) or about components inside the parts we buy (chips, wafers, panels)
  - unrelated topics and reports showing normal conditions

Rules:
- Use ONLY the information in the provided text. Never add numbers or dates from your own knowledge.
- Supplier IDs must be copied exactly from the supplier list.
- News may be written in ANY language. Read it in its original language, but write the reason, why and
  summary fields in English. In the summary keep qualifiers exactly as the text gives them ("at least",
  "up to", "about", "expected"). Translate them carefully, they have opposite meanings: Turkish
  "en az" = "at least", "en fazla" / "en cok" = "up to", "yaklasik" = "about". Never add a qualifier
  the text does not use: "expected to resume in three days" is "about three days", not "at least".
- Convert all dates to the Gregorian calendar in YYYY-MM-DD format (e.g. the Thai Buddhist
  Era year 2569 is 2026).
- Write numbers as plain numbers: "yuzde 10", "10%", "10 percent" and "百分之十" are all 10."""


SUPPLIER_FIELDS = (
    "id", "name", "part_en", "hs6", "origin_country", "assembly_countries",
    "trade_agreement_with_turkey", "transport_mode", "departure_point", "arrival_point",
)


def _supplier_payload(suppliers: list[dict]) -> list[dict]:
    """Supplier fields sent to the model; empty fields are left out to save tokens."""
    out = []
    for s in suppliers:
        row = {k: s[k] for k in SUPPLIER_FIELDS if s.get(k) not in (None, "", [])}
        hs6 = row.get("hs6", "")
        if len(hs6) == 6 and hs6.isdigit():
            row["hs6"] = f"{hs6[:4]}.{hs6[4:]}"  # 847330 -> 8473.30, as written in the news
        out.append(row)
    return out


def describe_company(company) -> str:
    """One-line company description from the 'company' field of suppliers.json."""
    if not company:
        return DEFAULT_COMPANY
    if isinstance(company, str):
        return company
    parts = [company.get("name"), company.get("sector"),
             ", ".join(x for x in (company.get("city"), company.get("country")) if x)]
    return " - ".join(p for p in parts if p) or DEFAULT_COMPANY


def _context(company) -> str:
    return COMMON_CONTEXT.format(company=describe_company(company))


def _schema_block(schema: dict | None) -> str:
    if schema is None:
        return ""
    return (
        "\n\nReturn ONLY a JSON object matching this JSON Schema, with no extra text:\n"
        + json.dumps(schema, ensure_ascii=False)
    )


def filter_messages(suppliers: list[dict], news_batch: list[dict], schema: dict | None, company=None):
    system = (
        _context(company)
        + "\n\nTASK: For EACH news item choose impact_level 'direct' or 'none'. "
        "Return one result per news item, in the same order. "
        "affected_supplier_ids: the suppliers the item affects (empty for 'none'). "
        "For 'none' use event_type 'not_relevant' and an empty list."
        + _schema_block(schema)
    )
    payload = {
        "suppliers": _supplier_payload(suppliers),
        "news": [
            {"id": n["id"], "title": n["title"], "date": n.get("date", ""), "text": n.get("full_text", "")}
            for n in news_batch
        ],
    }
    user = json.dumps(payload, ensure_ascii=False)
    return system, user


def analysis_messages(suppliers: list[dict], news: dict, schema: dict | None, company=None,
                      candidates: list[str] | None = None):
    """candidates: suppliers found by the filter. The analysis model checks each one, so it
    can drop a wrong candidate and add a missed one."""
    check = ""
    if candidates:
        check = (
            "A first screening flagged these supplier IDs as possibly affected: "
            f"{', '.join(candidates)}. Check EACH of them against the article and the supplier list: "
            "keep those that are affected, drop those that are not, and add any affected supplier it missed. "
        )
    system = (
        _context(company)
        + "\n\nTASK: Analyse the news article and extract structured facts. "
        "List every supplier it affects (it may be several or none). "
        + check +
        "If a tax rate or date is not explicitly stated, use null - do not guess. "
        "rate_type: the Turkish tax the rates belong to - 'gv' (customs duty), 'igv' (additional customs "
        "duty), 'kultur_fonu', 'kdv' (VAT) or 'otv'; null if it is not a tax or the text does not say. "
        "status: 'enacted' for measures that are decided - signed, published or officially announced - "
        "EVEN IF their effective date is in the future, and for price changes that happened; 'proposed' "
        "ONLY for drafts, measures open for comments, plans and proposals not yet decided; "
        "'ongoing_event' for transport disruptions; 'unclear' if the text does not say, and for forecast or "
        "expected price changes that have not happened yet. "
        "For ongoing events set effective_date to null. effective_date is the date the text gives for the "
        "measure to take effect; if the text gives none, use null - never the article's publication date, "
        "and do not say in the summary when it takes effect. "
        "affected_locations: for transport disruptions, the departure_point or arrival_point "
        "values the event hits, copied exactly from the supplier list (only points of the same kind as the "
        "one affected: an airport problem never lists a seaport); an empty list for other event types. "
        "expected_delay_days: for transport disruptions, the number of days shipments are expected to be "
        "delayed or stopped, ONLY if the text states a duration; convert weeks or hours to days and, for a "
        "range or 'at least' / 'up to', use the largest number. "
        "If no duration is stated, or for tariffs and other measures, use null. "
        "price_change_pct: for price changes, the change in percent with a sign (+40 up, -5 down), ONLY if "
        "the text states it; null otherwise. "
        "summary: 2-3 sentences in English for a procurement manager."
        + _schema_block(schema)
    )
    payload = {
        "suppliers": _supplier_payload(suppliers),
        "article": {k: news[k] for k in ("id", "title", "date", "full_text")},
    }
    user = json.dumps(payload, ensure_ascii=False)
    return system, user
