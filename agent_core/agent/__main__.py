"""Command-line entry point for the supply chain risk agent.

    python -m agent --db                            # new articles from the project database
    python -m agent --db --save                     # ... and store the results in the database
    python -m agent --news <news.json>              # articles from a JSON file
    python -m agent --news <news.json> --dry-run    # check the pipeline without API calls

Reads the articles and the supplier list, runs the pipeline and writes the results to
output/agent_results_<timestamp>.json (schema: agent/OUTPUT_FORMAT.md). With --save the
results are also written to article_analyses and article_impacts; without it a results file
can be checked first and stored later with: python -m agent.save <file>
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .env import ROOT, load_env
from .news_loader import load_news, load_news_db, load_suppliers
from .pipeline import Agent


def main():
    ap = argparse.ArgumentParser(description="Supply chain risk agent: news screening and impact analysis")
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--db", action="store_true", help="Read articles without an analysis from the database")
    source.add_argument("--news", help="News file in the news collector's format (JSON)")
    ap.add_argument("--suppliers", default=str(ROOT / "data" / "suppliers.json"), help="Supplier list")
    ap.add_argument("--out", help="Output file (default: output/agent_results_<timestamp>.json)")
    ap.add_argument("--config", help="Config file (default: agent/config.yaml)")
    ap.add_argument("--dry-run", action="store_true", help="Use placeholder answers instead of the API")
    ap.add_argument("--save", action="store_true", help="Store the results in the database (with --db)")
    args = ap.parse_args()
    if args.save and (not args.db or args.dry_run):
        ap.error("--save works only with --db and without --dry-run")

    load_env()
    news, warnings = load_news_db() if args.db else load_news(args.news)
    suppliers, company = load_suppliers(args.suppliers)
    for w in warnings:
        print("! " + w)
    print(f"Loaded {len(news)} articles and {len(suppliers)} suppliers" + (" (dry run)" if args.dry_run else ""))

    agent = Agent(args.config, mock=args.dry_run)
    output = agent.run(news, suppliers, company)
    output["run"]["input_warnings"] = warnings

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + ("-dryrun" if args.dry_run else "")
    out = Path(args.out) if args.out else ROOT / "output" / f"agent_results_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    run = output["run"]
    c = run["counts"]
    print(f"Relevant (alerts): {c['direct']} | Not relevant: {c['none']} | Errors: {c['error']}")
    print(f"Estimated cost: ${run['estimated_cost_usd']}")
    for r in output["results"]:
        for msg in r["errors"] + r["warnings"]:
            # Console shows the short form; the full reasoning stays in the JSON file
            print(f"  [{r['news_id']}] {msg.split(' Filter reason:')[0]}")
    print(f"Output -> {out}  (details in each article's 'warnings' field)")

    if args.save:
        from .save import store
        store(output["results"])


if __name__ == "__main__":
    main()
