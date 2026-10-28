"""
Main Entry Point Module:
Runs the whole chain in one go: news scan -> agent analysis -> cost impacts and alerts.

    python main.py               # full run (manual)
    python main.py --schedule    # same, recorded as a scheduled run (Scheduler.py, Task Scheduler)
    python main.py --no-agent    # scan only, the agent analyses the new news on the next run

Outputs:
    clean_news_only_report_final.json -> GIVEN TO THE MODEL (accepted news only)
    rejected_results_debug.json       -> developer only (rejected results + full report)
    scan_logs / articles tables       -> one row per scan, accepted news linked to it
    article_analyses / article_impacts-> agent results for every news without an analysis (agent_core)
    agent_core/output/*.json          -> agent results file of each run (for checking)
    cost_impacts / alerts tables      -> refreshed after a successful scan (risk_alerts.py)
    notification                      -> important new / changed alerts to Slack, e-mail ... (notify.py)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from analyzer import CleanNewsOnlySupplyAnalyzer
from article_store import save_articles
from models import FinalCleanSupplyReport
from notify import send_alerts
from panel_sync import sync_panel
from risk_alerts import update_risks
from scan_log import ScanFailed, scan_log, scheduled_scan_due

# All paths are relative to this file, so the scan works no matter
# which folder it is started from (e.g. by a scheduler or Task Scheduler)
HERE = Path(__file__).resolve().parent
SEARCH_PLAN_PATH = HERE / "search_plan.json"                  # produced by query_planner.py
OUTPUT_PATH = HERE / "clean_news_only_report_final.json"      # file given to the model
DEBUG_PATH = HERE / "rejected_results_debug.json"             # debug file, not given to the model
AGENT_DIR = HERE / "agent_core"                               # the agent package lives in agent_core/agent
SUPPLIERS_PATH = AGENT_DIR / "data" / "suppliers.json"        # supplier list the agent matches news against
AGENT_OUTPUT_DIR = AGENT_DIR / "output"                       # agent results file of every run

# Load TAVILY_API_KEY, NEBIUS_API_KEY and POSTGRES_* from the .env file (keys are never written in the code)
load_dotenv(HERE / ".env")
sys.path.insert(0, str(AGENT_DIR))


def _write_atomic(path: Path, text: str) -> None:
    """Write to a temporary file first, then replace the target in one step.
    This way the model never reads a half-written JSON while a scan is running."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def run_agent() -> None:
    """Agent step: every article without an analysis (this scan's new news and any left over
    from a failed run) -> article_analyses / article_impacts. Alerts are refreshed by run_scan."""
    if not os.getenv("NEBIUS_API_KEY"):
        print("[!] NEBIUS_API_KEY tanımlı değil, ajan analizi atlandı (haberler sonraki çalışmada analiz edilir)")
        return
    from agent.news_loader import connect, load_news_db, load_suppliers
    from agent.pipeline import Agent
    from agent.save import save

    news, warnings = load_news_db()
    if not news:
        print("[✓] Ajan: analiz bekleyen haber yok")
        return
    suppliers, company = load_suppliers(SUPPLIERS_PATH)
    print(f"Ajan: {len(news)} haber, {len(suppliers)} tedarikçi analiz ediliyor...")
    output = Agent().run(news, suppliers, company)
    output["run"]["input_warnings"] = warnings

    AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = AGENT_OUTPUT_DIR / f"agent_results_{datetime.now():%Y%m%d-%H%M%S}.json"
    _write_atomic(out, json.dumps(output, ensure_ascii=False, indent=2))

    # One transaction: if any row fails nothing is stored and the news are analysed again next run
    with connect() as conn:
        analyses, impacts, messages = save(output["results"], conn)
    for m in messages:
        print("    ! " + m)
    run = output["run"]
    c = run["counts"]
    print(f"[✓] Ajan: {c['direct']} ilgili | {c['none']} ilgisiz | {c['error']} hata | "
          f"{analyses} analiz, {impacts} etki kaydedildi | ~${run['estimated_cost_usd']} | {out.name}")


def run_scan(triggered_by: str = "manual", with_agent: bool = True) -> FinalCleanSupplyReport:
    """Run one full scan, write both JSON files and record it in scan_logs / articles,
    then analyse the new news with the agent and refresh the alerts.
    Raises an exception instead of exiting, so the scheduler can keep running after an error."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY tanımlı değil (.env dosyasını kontrol edin).")
    if not SEARCH_PLAN_PATH.exists():
        raise FileNotFoundError(f"{SEARCH_PLAN_PATH.name} bulunamadı (önce query_planner.py çalıştırın).")

    # Initialize the supply chain analyzer instance
    analyzer = CleanNewsOnlySupplyAnalyzer(
        tavily_api_key=api_key,
        search_plan_path=str(SEARCH_PLAN_PATH),
        company_country="Turkey",
    )

    # Every scan is recorded in scan_logs: 'running' -> 'success' / 'failed'
    with scan_log(triggered_by) as scan:
        # Run all queries in the search plan
        report = analyzer.execute_scan()

        # Write the model file (trimmed fields) and the debug file (rejections + full report)
        _write_atomic(OUTPUT_PATH, analyzer.export_to_json(report))
        _write_atomic(DEBUG_PATH, analyzer.export_rejections(report))

        # Summarize execution statistics and results
        found = sum(1 for r in report.reports if r.status == "Events Found")
        errors = sum(1 for r in report.reports if r.status == "Search Error")
        news = sum(len(r.sources_found) for r in report.reports)
        print(f"[✓] {len(report.reports)} sorgu | {news} haber ({found} sorguda) | {errors} arama hatası "
              f"| {len(analyzer.rejections)} sonuç elendi")
        print(f"    Model için rapor: {OUTPUT_PATH.name} | Elenenler (debug): {DEBUG_PATH.name}")

        # Summary counts go to the same scan_logs row
        scan.set_counts(
            query_count=len(report.reports),
            found_count=news,
            rejected_count=len(analyzer.rejections),
            error_count=errors,
        )

        # Accepted news go to articles, linked to this scan (skipped if scan_logs was unreachable)
        if scan.id is not None:
            saved = save_articles(scan.id, report)
            print(f"[✓] {len(saved)} haber articles tablosuna kaydedildi")

        # Every query failing means the search itself is broken (API key, network)
        if report.reports and errors == len(report.reports):
            raise ScanFailed(f"{errors} sorgunun hepsi arama hatası verdi")

    # The scan is now 'success'. The agent analyses its news; a failed agent does not fail the
    # scan (the news stay without an analysis and are picked up by the next run).
    if scan.id is not None and with_agent:
        try:
            run_agent()
        except Exception as e:
            print(f"[!] Ajan analizi başarısız (tarama kaydedildi): {type(e).__name__}: {e}")

    # Refresh cost_impacts / alerts / alert_articles with the new analyses
    if scan.id is not None:
        try:
            update_risks(scan.id)
        except Exception as e:
            print(f"[!] Alert'ler güncellenemedi (tarama kaydedildi): {type(e).__name__}: {e}")

    # New / changed / resolved alerts -> panel events and its notification bell (unsent ones are retried next run)
    if scan.id is not None:
        try:
            sync_panel()
        except Exception as e:
            print(f"[!] Panele gönderilemedi: {type(e).__name__}: {e}")

    # Important new / changed alerts -> Slack, Teams, e-mail ... (unsent ones are retried next run)
    if scan.id is not None:
        try:
            send_alerts()
        except Exception as e:
            print(f"[!] Bildirim gönderilemedi: {type(e).__name__}: {e}")
    return report


def main():
    # Runs started by cron / Task Scheduler pass --schedule; everything else is manual
    triggered_by = "schedule" if "--schedule" in sys.argv else "manual"
    # The Task Scheduler wakes up every hour; the interval itself is set in the panel (Ayarlar)
    if triggered_by == "schedule":
        due, why = scheduled_scan_due()
        print(f"[{datetime.now():%Y-%m-%d %H:%M}] " + (f"Tarama başlıyor ({why})" if due else f"Tarama atlandı ({why})"))
        if not due:
            return
    try:
        run_scan(triggered_by, with_agent="--no-agent" not in sys.argv)
    except ScanFailed as e:
        sys.exit(f"[!] Tarama başarısız: {e}")
    except (RuntimeError, FileNotFoundError) as e:
        sys.exit(f"[!] {e}")


if __name__ == "__main__":
    main()
