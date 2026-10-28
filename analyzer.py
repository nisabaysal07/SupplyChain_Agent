"""
Supply Chain News Analyzer Module:
Core orchestrator that reads search plans, executes Tavily web searches across official
and news domains, filters/validates articles based on relevance rules, and compiles final reports.

Module layout:
    models.py     -> output schema (dataclasses)
    text_utils.py -> text cleaning, sentence splitting, summary building
    sources.py    -> domain / URL / date checks and the Tavily search call
    relevance.py  -> relevance rules (logistics, country pair, single country)
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import List, Optional

from tavily import TavilyClient

import config as cfg
import relevance
import sources
import text_utils
from models import NewsSourceItem, SupplierNewsReport, FinalCleanSupplyReport


# Fields kept in the JSON that is given to the model.
# All other fields stay available in the debug file under "full_report".
MODEL_REPORT_FIELDS = (
    "query_type",        # event type: logistics | tariff | import_restriction | export_control | agreement
    "supplier_country",  # supplier country (null for logistics queries)
    "logistics_point",   # port / airport (null for trade queries)
    "supplier_names",    # affected suppliers
    "products",          # affected products
    "status",            # Events Found | No Relevant News Found | Search Error
)
MODEL_NEWS_FIELDS = ("news_id", "title", "published_date", "source_name", "url", "summary")


class CleanNewsOnlySupplyAnalyzer:
    """Main analyzer class responsible for executing automated supply chain news scans and filtering."""

    def __init__(self, tavily_api_key: str, search_plan_path: str,
                 company_country: str = "Turkey", client=None):
        self.client = client or TavilyClient(api_key=tavily_api_key)
        self.default_company_country = company_country
        self.rejections: List[dict] = []     # rejected results with reasons (debug only)
        with open(search_plan_path, "r", encoding="utf-8") as f:
            self.search_plan = json.load(f)

    # ------------------------------------------------------------------ single query
    def _process_item(self, item: dict) -> SupplierNewsReport:
        """Process a single query item from the search plan, run searches, and filter results."""
        q_id = item.get("query_id", "?")
        company = item.get("company_country") or self.search_plan.get("company_country") or self.default_company_country
        country = item.get("supplier_country") or item.get("country")
        logistics_point = item.get("logistics_point")
        qtype = relevance.infer_query_type(item, company, country)
        mode = relevance.relevance_mode(qtype, company, country)

        products = list(dict.fromkeys(item.get("products") or []))
        ctx = relevance.build_context(mode, qtype, company, country, logistics_point, products)

        # Sources of the company's own country (e.g. Anadolu Agency, Official Gazette) are always included
        countries = [company] + ([country] if country else [])
        official, news = sources.domains_for(
            countries, include_trade_press=(mode == "logistics" and cfg.USE_TRADE_PRESS_FOR_LOGISTICS)
        )

        print(f"-> [{q_id}] {qtype} | {logistics_point or f'{company} <-> {country or chr(8212)}'}")

        # 1) Execute search queries via Tavily API (official sites + news agencies)
        raw_results, errors = [], []
        for q in sources.build_queries(item, qtype):
            for topic, domains in (("general", official), ("news", news)):
                res, err = sources.tavily_search(self.client, q, domains, topic)
                raw_results.extend(res)
                if err:
                    errors.append(err)

        # 2) Filter and validate raw search results
        found = self._filter_results(raw_results, q_id, ctx, official, news)

        # 3) Sort results: official sources first, followed by newest publication date
        found.sort(key=lambda s: s.published_date or "", reverse=True)
        found.sort(key=lambda s: s.source_type != "official")
        for i, s in enumerate(found, start=1):
            s.news_id = f"{q_id}-N{i}"

        # "No Relevant News Found" means no qualifying news, NOT "no risk"
        if found:
            status = "Events Found"
        elif errors and not raw_results:
            status = "Search Error"
        else:
            status = "No Relevant News Found"

        return SupplierNewsReport(
            query_id=q_id,
            query=item.get("query", ""),
            query_type=qtype,
            priority=item.get("priority"),
            company_country=company,
            supplier_country=None if mode == "logistics" else (country or "Global"),
            logistics_point=logistics_point,
            location_country=country if mode == "logistics" else None,
            supplier_names=list(dict.fromkeys(item.get("supplier_names") or [])),
            products=products,
            status=status,
            search_errors=errors,
            sources_found=found,
        )

    # ------------------------------------------------------------------ filter pipeline
    def _filter_results(self, raw_results: list, q_id: str, ctx: dict,
                        official: List[str], news: List[str]) -> List[NewsSourceItem]:
        """Apply strict filtering pipeline (whitelist, scores, date recency, and relevance evaluation)."""
        now = datetime.now(timezone.utc)
        found, seen_urls = [], set()
        allowed = official + news
        for res in raw_results:
            url, title = res.get("url", ""), text_utils.normalize(res.get("title", ""))
            reject = lambda reason: self.rejections.append({"query_id": q_id, "reason": reason, "title": title, "url": url})

            # Skip duplicates (same article returned by several searches)
            canon = sources.canonical_url(url)
            if canon in seen_urls:
                continue
            seen_urls.add(canon)

            # Only whitelisted official / trusted domains are accepted
            domain = sources.match_domain(url, allowed)
            if not domain:
                reject("domain_not_whitelisted"); continue
            if not sources.is_valid_article_url(url, title):
                reject("bad_url_or_title"); continue

            # Tavily relevance score threshold
            score = res.get("score")
            min_score = cfg.STRICT_MIN_TAVILY_SCORE if cfg.STRICT_MODE else cfg.MIN_TAVILY_SCORE
            if score is not None and score < min_score:
                reject(f"low_score_{score:.2f}"); continue

            # Enforce strict recency window (cfg.MAX_AGE_HOURS, default 48 hours)
            pub = sources.parse_date(res.get("published_date"))
            if pub is None:
                if cfg.REJECT_UNDATED:
                    reject("no_publish_date"); continue
            else:
                age_h = (now - pub).total_seconds() / 3600
                if age_h > cfg.MAX_AGE_HOURS:
                    reject(f"too_old_{age_h:.0f}h"); continue
                if age_h < -24:
                    reject("future_date"); continue

            # Content-level relevance rules (location / countries / trade terms in the same sentence)
            sentences = text_utils.extract_sentences(res.get("content", ""), res.get("raw_content") or "")
            ok, reason, hits = relevance.evaluate(ctx, title, sentences, domain)
            if not ok:
                reject(reason); continue

            # Summary is built only from matching sentences (+ one short follow-up sentence)
            summary = text_utils.build_summary(text_utils.with_context(hits, sentences))
            if len(summary) < 80:
                reject("summary_too_short"); continue

            found.append(NewsSourceItem(
                news_id="",
                title=title,
                published_date=pub.strftime("%Y-%m-%d") if pub else None,
                date_verified=pub is not None,
                effective_date=text_utils.extract_effective_date(
                    (res.get("content") or "") + " " + (res.get("raw_content") or "")[: cfg.MAX_TEXT_CHARS],
                    pub.date() if pub else None,
                ),
                source_name=cfg.SOURCE_DISPLAY_NAMES.get(domain, domain),
                source_type=sources.source_type_of(domain, official),
                url=url,
                relevance=reason,
                summary=summary,
            ))
        return found

    # ------------------------------------------------------------------ public interface (main.py)
    def execute_scan(self, limit: Optional[int] = None) -> FinalCleanSupplyReport:
        """Run all queries in the search plan (optionally only the first `limit` queries)."""
        queries = self.search_plan.get("queries", [])
        if limit:
            queries = queries[:limit]
        print(f"[*] Tarama başladı ({len(queries)} sorgu)...")
        reports = [self._process_item(item) for item in queries]
        return FinalCleanSupplyReport(
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            plan_generated_at=self.search_plan.get("generated_at"),
            reports=reports,
        )

    def export_to_json(self, report: FinalCleanSupplyReport) -> str:
        """JSON GIVEN TO THE MODEL: accepted news only, with the fields the model needs."""
        model_view = {
            "reports": [
                {
                    **{k: rep[k] for k in MODEL_REPORT_FIELDS},
                    "sources_found": [{k: news[k] for k in MODEL_NEWS_FIELDS} for news in rep["sources_found"]],
                }
                for rep in asdict(report)["reports"]
            ]
        }
        return json.dumps(model_view, ensure_ascii=False, indent=2)

    def export_rejections(self, report: Optional[FinalCleanSupplyReport] = None) -> str:
        """Developer-only debug JSON. NOT given to the model.
        - by_query: rejected results and the reason for each rejection
        - full_report: the complete report with all fields (relevance, search_errors, date_verified ...)"""
        grouped = {}
        for r in self.rejections:
            grouped.setdefault(r["query_id"], []).append(
                {"reason": r["reason"], "title": r["title"], "url": r["url"]}
            )
        data = {"total": len(self.rejections), "by_query": grouped}
        if report is not None:
            data["full_report"] = asdict(report)
        return json.dumps(data, ensure_ascii=False, indent=2)