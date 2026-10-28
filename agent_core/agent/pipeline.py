"""Two-stage pipeline: screening filter -> impact analysis -> impact score.

1. Filter (Nemotron 3 Super): every article is screened on its own and marked
   relevant ('direct') or not ('none'), with its event type and affected suppliers.
2. Analysis (Nemotron 3 Ultra): only relevant articles. The filter's suppliers are
   passed in as candidates; Ultra checks each one and extracts rates, dates,
   status, expected delay, an English summary and a supporting quote.
3. Score: computed in code from the status and the size of the event (agent/scoring.py).

Ultra also acts as a second check: if it finds an article irrelevant, the alert is
dropped; if its suppliers or event type differ from the filter's, its answer is used
and a warning is recorded. Supplier ids and locations not in the supplier list are discarded.
The cheap model screens everything and the larger one only sees the few articles
that matter, which keeps a run to a few cents. Costs and stock effects are computed
by the cost module from this output, not here.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .llm_client import CallResult, LLMClient
from .prompts import analysis_messages, filter_messages
from .schemas import FilterBatch, ImpactAnalysis, prompt_schema
from .scoring import impact_score, is_relevant

SCHEMA_VERSION = "1.3"
DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")


def _chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _route_points(suppliers) -> set[str]:
    """Departure and arrival points named in the supplier list (a field may hold a list)."""
    points = set()
    for s in suppliers:
        for key in ("departure_point", "arrival_point"):
            value = s.get(key)
            points.update(value if isinstance(value, list) else [value] if value else [])
    return points


# Placeholder answers for --dry-run (no API calls)

def _mock_filter(batch, suppliers):
    out = []
    for n in batch:
        text = f"{n['title']} {n['full_text']}".lower()
        hit = [s["id"] for s in suppliers
               if any(w and w.lower() in text for w in (s.get("departure_point"), s.get("arrival_point"),
                                                         s.get("origin_country")))]
        out.append({"news_id": n["id"], "impact_level": "direct" if hit else "none",
                    "affected_supplier_ids": hit,
                    "event_type": "other" if hit else "not_relevant", "reason": "dry run"})
    return {"results": out}


def _mock_analysis(n, supplier_ids):
    draft = re.search(r"draft|propos|plan|taslak", f"{n['title']} {n['full_text']}".lower())
    return {"affected_suppliers": [{"supplier_id": s, "why": "dry run"} for s in supplier_ids],
            "event_type": "other", "status": "proposed" if draft else "unclear", "country": None,
            "affected_locations": [],
            "rate_type": None,
            "old_rate_pct": None, "new_rate_pct": None, "effective_date": None,
            "expected_delay_days": None, "price_change_pct": None,
            "summary": "dry run", "evidence_quote": n["title"]}


class Agent:
    def __init__(self, config_path: str | Path | None = None, mock: bool = False):
        self.config = yaml.safe_load(Path(config_path or DEFAULT_CONFIG).read_text(encoding="utf-8"))
        self.mock = mock
        self.filter_client = LLMClient(self.config, "filter", mock=mock)
        self.analysis_client = LLMClient(self.config, "analysis", mock=mock)
        self.usage = {"filter": [], "analysis": []}

    def run(self, news: list[dict], suppliers: list[dict], company=None) -> dict:
        started = _now()
        known_ids = {s["id"] for s in suppliers}
        self.known_points = _route_points(suppliers)
        results = {n["id"]: self._empty_result(n) for n in news}

        # Stage 1: filter. Batch size 1 by default: in larger batches the model
        # occasionally left an article out of its answer.
        batch_size = self.config["pipeline"]["filter_batch_size"]
        schema = prompt_schema(FilterBatch)
        for batch in _chunks(news, batch_size):
            system, user = filter_messages(suppliers, batch, schema, company)
            res = self.filter_client.call(system, user, FilterBatch,
                                          mock_response=_mock_filter(batch, suppliers))
            self.usage["filter"].append(res)
            preds = {p.news_id: p for p in res.parsed.results} if res.ok else {}
            for n in batch:
                self._apply_filter(results[n["id"]], preds.get(n["id"]), res, known_ids)

        # Stage 2: analysis of relevant articles only
        schema = prompt_schema(ImpactAnalysis)
        for n in news:
            r = results[n["id"]]
            if r["impact_level"] != "direct":
                continue
            system, user = analysis_messages(suppliers, n, schema, company,
                                             candidates=r["affected_supplier_ids"])
            res = self.analysis_client.call(system, user, ImpactAnalysis,
                                            mock_response=_mock_analysis(n, r["affected_supplier_ids"]))
            self.usage["analysis"].append(res)
            self._apply_analysis(r, res, known_ids)

        # Stage 3: impact score
        for r in results.values():
            r["impact_score"] = impact_score(r["impact_level"], r["analysis"], r["event_type"],
                                             len(r["affected_supplier_ids"]))
            r["is_relevant"] = is_relevant(r["impact_score"])

        return {
            "schema_version": SCHEMA_VERSION,
            "run": self._run_info(started, list(results.values())),
            "results": list(results.values()),
        }

    @staticmethod
    def _empty_result(n: dict) -> dict:
        db_ids = {k: n[k] for k in ("article_id", "scan_log_id") if k in n}  # database mode only
        return {
            "news_id": n["id"],
            **db_ids,
            "title": n["title"],
            "source_name": n.get("source_name"),
            "source_url": n.get("url"),
            "published_at": n.get("published_at"),
            "impact_level": None,
            "impact_score": None,
            "is_relevant": None,
            "affected_supplier_ids": [],
            "event_type": None,
            "filter_reason": None,
            "analysis": None,
            "warnings": [],
            "errors": [],
        }

    @staticmethod
    def _keep_known(ids, known_ids, r, where) -> list[str]:
        """Drops supplier ids that are not in the supplier list."""
        unknown = [i for i in ids if i not in known_ids]
        if unknown:
            r["warnings"].append(f"{where}: unknown supplier id removed: {', '.join(unknown)}")
        return sorted({i for i in ids if i in known_ids})

    def _apply_filter(self, r: dict, pred, res: CallResult, known_ids: set):
        if pred is None:
            r["errors"].append("filter: " + (res.error or "article missing from the model's answer"))
            return
        r["impact_level"] = pred.impact_level
        r["event_type"] = pred.event_type
        r["filter_reason"] = pred.reason
        affected = self._keep_known(pred.affected_supplier_ids, known_ids, r, "filter")
        r["affected_supplier_ids"] = affected if pred.impact_level == "direct" else []
        if pred.impact_level == "direct" and not r["affected_supplier_ids"]:
            r["warnings"].append("filter: marked relevant but no valid supplier id")

    def _apply_analysis(self, r: dict, res: CallResult, known_ids: set):
        if not res.ok:
            r["errors"].append("analysis: " + (res.error or "unknown error"))
            return
        a = res.parsed.model_dump()
        if a["event_type"] == "not_relevant":
            # Second check: the analysis model found the article irrelevant, so the alert is dropped
            r["warnings"].append("filter marked relevant, analysis found it not relevant; alert dropped. "
                                 f"Filter reason: {r['filter_reason']} | Analysis: {a['summary']}")
            r["impact_level"] = "none"
            r["event_type"] = "not_relevant"
            r["affected_supplier_ids"] = []
            r["analysis"] = None
            return
        valid = set(self._keep_known([s["supplier_id"] for s in a["affected_suppliers"]],
                                     known_ids, r, "analysis"))
        a["affected_suppliers"] = [s for s in a["affected_suppliers"] if s["supplier_id"] in valid]
        unknown = [p for p in a["affected_locations"] if p not in self.known_points]
        if unknown:
            r["warnings"].append(f"analysis: unknown location removed: {', '.join(unknown)}")
        a["affected_locations"] = list(dict.fromkeys(p for p in a["affected_locations"] if p in self.known_points))
        r["analysis"] = a
        if r["impact_level"] == "direct":
            # On disagreement the analysis model's suppliers and event type are used
            if valid and valid != set(r["affected_supplier_ids"]):
                r["warnings"].append(
                    f"filter and analysis found different suppliers (filter: {' '.join(r['affected_supplier_ids']) or '-'}, "
                    f"analysis: {' '.join(sorted(valid))}); analysis used")
                r["affected_supplier_ids"] = sorted(valid)
            if a["event_type"] != r["event_type"]:
                r["warnings"].append(f"filter and analysis found different event types (filter: {r['event_type']}, "
                                     f"analysis: {a['event_type']}); analysis used")
                r["event_type"] = a["event_type"]

    def _run_info(self, started: str, results: list[dict]) -> dict:
        def usage(task):
            calls = self.usage[task]
            m = self.config["models"][task]
            tin = sum(c.prompt_tokens for c in calls)
            tout = sum(c.completion_tokens for c in calls)
            return {"model_id": m["model_id"], "calls": len(calls),
                    "failed_calls": sum(not c.ok for c in calls),
                    "prompt_tokens": tin, "completion_tokens": tout,
                    "estimated_cost_usd": round((tin * m["price_in"] + tout * m["price_out"]) / 1e6, 5)}

        counts = {lvl: sum(r["impact_level"] == lvl for r in results) for lvl in ("direct", "none")}
        counts["error"] = sum(r["impact_level"] is None for r in results)
        counts["total"] = len(results)
        f, a = usage("filter"), usage("analysis")
        return {"started_at": started, "finished_at": _now(), "mock": self.mock,
                "counts": counts, "filter": f, "analysis": a,
                "estimated_cost_usd": round(f["estimated_cost_usd"] + a["estimated_cost_usd"], 5)}
