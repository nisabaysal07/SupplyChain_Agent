"""
Sources and Search Layer Module:
Handles domain whitelisting, URL validation, publication date parsing, 
Tavily API calls, and search query generation.
"""

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

import config as cfg
from text_utils import fold


def domains_for(countries: List[str], include_trade_press: bool) -> Tuple[List[str], List[str]]:
    """Retrieve allowed official and news agency domains based on target countries."""
    official = list(cfg.OFFICIAL_DOMAINS.get("Global", []))
    news = list(cfg.NEWS_AGENCY_DOMAINS.get("Global", []))
    for c in countries:
        official += cfg.OFFICIAL_DOMAINS.get(c, [])
        news += cfg.NEWS_AGENCY_DOMAINS.get(c, [])
    if include_trade_press:
        news += cfg.TRADE_PRESS_DOMAINS
    return sorted(set(official)), sorted(set(news))


def host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def match_domain(url: str, domains: List[str]) -> Optional[str]:
    """Match domain using suffix matching including subdomains (prevents fake domains like 'reuters.com.fake.xyz')."""
    h = host(url)
    for d in sorted(domains, key=len, reverse=True):
        if h == d or h.endswith("." + d):
            return d
    return None


def canonical_url(url: str) -> str:
    """Normalize a URL to its canonical form by stripping trailing slashes and query parameters."""
    p = urlparse(url)
    return urlunparse((p.scheme, (p.hostname or "").lower(), p.path.rstrip("/"), "", "", ""))


def is_valid_article_url(url: str, title: str) -> bool:
    p = urlparse(url)
    if p.path.strip("/") == "":
        return False
    ul, tl = url.lower(), fold(title)
    if any(b in ul for b in cfg.BAD_URL_PATTERNS):
        return False
    if any(b in tl for b in cfg.BAD_TITLE_PATTERNS):
        return False
    return True


def source_type_of(domain: str, official: List[str]) -> str:
    if domain in official:
        return "official"
    if domain in cfg.TRADE_PRESS_DOMAINS:
        return "trade_press"
    return "news_agency"



def parse_date(raw: Optional[str]) -> Optional[datetime]:
    """Parse raw date strings into timezone-aware datetime objects."""
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        dt = None
    if dt is None:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(raw[:10], "%Y-%m-%d")
            except ValueError:
                return None  # ESKİ KOD: bugünün tarihini uyduruyordu
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def tavily_search(client, query: str, domains: List[str], topic: str) -> Tuple[list, Optional[str]]:
    """"Execute a Tavily search query with domain filters and topic settings."""
    if not domains:
        return [], None
    params = dict(
        query=query, include_domains=domains, topic=topic,
        search_depth=cfg.SEARCH_DEPTH, max_results=cfg.MAX_RESULTS_PER_PASS,
        include_raw_content=True,
    )
    if topic == "news":
        params["days"] = max(1, -(-cfg.MAX_AGE_HOURS // 24))   # 48 saat -> 2 gün
    else:
        params["time_range"] = "week"   # general aramada saat bazlı filtre yok
    try:
        return client.search(**params).get("results", []), None
    except TypeError:
        params.pop("time_range", None)  # eski tavily-python sürümleri
        try:
            return client.search(**params).get("results", []), None
        except Exception as e:
            return [], f"{topic}: {e}"
    except Exception as e:
        return [], f"{topic}: {e}"


def build_queries(item: dict, qtype: str) -> List[str]:
    base = item.get("query", "")
    if qtype == "logistics":
        if cfg.STRICT_MODE:
            base = re.sub(r"\s*\([^)]*\)", "", base).strip()
        else:
            point = re.sub(r"\s*\([^)]*\)", "", item.get("logistics_point") or "")
            base = f"{point} port airport strike closure disruption delay weather"
    queries = [base]
    if cfg.ADD_TURKIYE_QUERY_VARIANT and not cfg.STRICT_MODE and re.search(r"\bTurkey\b", base):
        queries.append(re.sub(r"\bTurkey\b", "Türkiye", base))
    return queries