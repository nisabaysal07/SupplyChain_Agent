"""
Relevance Evaluation Module:
Determines query types, constructs matching contexts, and evaluates whether 
retrieved news articles meet the filtering criteria for supply chain reporting.
"""

import re
from typing import List, Optional, Tuple

import config as cfg
from text_utils import (
    fold, compile_terms, has,
    DISRUPTION_PAT, SEVERE_PAT, TRADE_PAT, RESTRICTION_PAT, SECTOR_PAT,
    NOISE_TITLE_PAT, COMMODITY_TITLE_PAT, COUNTRY_PATS,
)

_GENERIC_LOCATION_WORDS = {
    "port", "of", "the", "airport", "international", "terminal", "container", "harbour",
    "harbor", "limanı", "havalimanı", "uluslararası",
}


def infer_query_type(item: dict, company: str, country: Optional[str]) -> str:
    """Infer the specific category/type of the search query based on its content."""
    if item.get("query_type"):
        return item["query_type"]
    if item.get("logistics_point"):
        return "logistics"
    q = fold(item.get("query", ""))
    if "agreement" in q:
        return "agreement"
    if "export restriction" in q or "export control" in q:
        return "export_control"
    if "import duty" in q or "tariff" in q:
        return "tariff"
    if "import restriction" in q:
        return "import_restriction"
    return "trade"


def relevance_mode(qtype: str, company: str, supplier: Optional[str]) -> str:
    """Determine the evaluation mode (logistics, country pair, or single country)."""
    if qtype == "logistics":
        return "logistics"
    if qtype in ("import_restriction", "export_control"):
        return "single_country"
    if supplier and supplier != company:
        return "country_pair"
    return "single_country"


def logistics_aliases(point: str) -> List[str]:
    """Generate normalized search aliases for ports or airports by stripping generic terms."""
    if point in cfg.LOGISTICS_ALIASES:
        return cfg.LOGISTICS_ALIASES[point]
    
    country_words = {fold(a) for als in cfg.COUNTRY_ALIASES.values() for a in als}
    aliases = []
    paren = re.findall(r"\(([^)]+)\)", point)
    main = re.sub(r"\([^)]*\)", " ", point)
    words = [w for w in fold(main).split() if w not in _GENERIC_LOCATION_WORDS and w not in country_words]
    if words:
        phrase = " ".join(words)
        aliases.append(phrase)
        if "-" in phrase:
            aliases.extend(p for p in phrase.split("-") if len(p) >= 4)
    aliases.extend(fold(p) for p in paren)
    return aliases or [fold(point)]


def build_context(mode: str, qtype: str, company: str, country: Optional[str],
                  logistics_point: Optional[str], products: List[str]) -> dict:
    """Build a context dictionary containing regex patterns and domain filters for evaluation."""
    return {
        "mode": mode,
        "qtype": qtype,
        "location_country": country if mode == "logistics" else None,
        "company_pat": COUNTRY_PATS.get(company) or compile_terms([company]),
        "supplier_pat": (COUNTRY_PATS.get(country) or compile_terms([country])) if country else None,
        "country_pat": (COUNTRY_PATS.get(country) or compile_terms([country])) if country else None,
        "loc_pat": compile_terms(logistics_aliases(logistics_point)) if logistics_point else None,
        "company_official_domains": set(cfg.OFFICIAL_DOMAINS.get(company, [])),
    }


# karar
def evaluate(ctx: dict, title: str, sentences: List[str], domain: str) -> Tuple[bool, str, List[str]]:
    """Evaluate article relevance against context rules. Returns (is_accepted, reason, matched_sentences)."""
    t = fold(title)
    fs = [(s, fold(s)) for s in sentences]
    full = t + " " + " ".join(f for _, f in fs)
    mode = ctx["mode"]

    # Filter out general noise or unrelated commodity stories
    if has(NOISE_TITLE_PAT, t):
        return False, "noise_title", []
    if mode != "logistics" and has(COMMODITY_TITLE_PAT, t) and not has(SECTOR_PAT, full):
        return False, "commodity_story_without_sector", []

    if mode == "logistics":
        return _evaluate_logistics(ctx, t, fs, full)
    if mode == "country_pair":
        return _evaluate_country_pair(ctx, t, fs, domain)
    if mode == "single_country":
        return _evaluate_single_country(ctx, fs, full)
    return False, "unknown_mode", []


def _evaluate_logistics(ctx, t, fs, full):
    """Evaluate articles specifically for port/airports disruptions."""
    loc, ctry = ctx["loc_pat"], ctx["country_pat"]
    hits = [s for s, f in fs if has(loc, f) and has(DISRUPTION_PAT, f)]
    if has(loc, t) and (has(DISRUPTION_PAT, t) or hits):
        return True, "location_named_in_title_with_disruption", hits or [s for s, f in fs if has(loc, f)]

    # Reject if headline mentions a foreign country while target location country is missing
    foreign_in_title = any(has(p, t) for c, p in COUNTRY_PATS.items() if c != ctx["location_country"])
    if foreign_in_title and not has(ctry, full):
        return False, "foreign_country_event_location_country_absent", []
    if hits:
        return True, "location_and_disruption_in_same_sentence", hits
    if cfg.REQUIRE_LOCATION_NAME:
        return False, "location_name_not_mentioned", []
    if has(ctry, t) and has(SEVERE_PAT, t):
        hits = [s for s, f in fs if has(SEVERE_PAT, f) or has(DISRUPTION_PAT, f)]
        return True, "country_wide_severe_event", hits
    return False, "no_location_disruption_match", []


def _evaluate_country_pair(ctx, t, fs, domain):
    """Evaluate bilateral trade relations and agreements between two countries."""
    comp, supp = ctx["company_pat"], ctx["supplier_pat"]
    hits = [s for s, f in fs if has(comp, f) and has(supp, f) and has(TRADE_PAT, f)]
    if hits:
        return True, "both_countries_and_trade_term_in_same_sentence", hits
    if cfg.PAIR_SAME_SENTENCE_ONLY:
        if domain in ctx["company_official_domains"]:
            hits = [s for s, f in fs if has(supp, f) and has(TRADE_PAT, f)]
            if hits:
                return True, "company_country_official_source_mentions_supplier", hits
        return False, "countries_not_in_same_sentence_with_trade_term", []
    
    # Check adjacent sentence window to prevent cross-paragraph noise
    for i in range(len(fs) - 1):
        w = fs[i][1] + " " + fs[i + 1][1]
        if has(comp, w) and has(supp, w) and has(TRADE_PAT, w):
            hits.extend(x for x in (fs[i][0], fs[i + 1][0]) if x not in hits)
    if hits:
        return True, "both_countries_and_trade_term_in_adjacent_sentences", hits
    
    if has(comp, t) or has(supp, t):
        other = supp if has(comp, t) else comp
        hits = [s for s, f in fs if has(other, f) and has(TRADE_PAT, f)]
        if hits and has(TRADE_PAT, t + " " + " ".join(f for _, f in fs[:3])):
            return True, "one_country_in_title_other_in_trade_sentence", hits
    
    if domain in ctx["company_official_domains"]:
        hits = [s for s, f in fs if has(supp, f) and has(TRADE_PAT, f)]
        if hits:
            return True, "company_country_official_source_mentions_supplier", hits
    return False, "countries_not_cooccurring_with_trade_term", []


def _evaluate_single_country(ctx, fs, full):
    """Evaluate domestic trade restrictions or controls for a single country."""
    ctry = ctx["country_pat"]
    term = RESTRICTION_PAT if ctx["qtype"] in ("import_restriction", "export_control") else TRADE_PAT
    hits = [s for s, f in fs if has(ctry, f) and (has(term, f) or has(TRADE_PAT, f))]
    if hits and has(SECTOR_PAT, full):
        return True, "country_restriction_with_sector_term", hits
    return False, "no_country_restriction_for_sector", []

