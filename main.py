"""
Main Entry Point Module:
Loads environment variables, validates configuration files, initializes
the supply chain analyzer, executes the scan, and exports final reports and debug logs.

Outputs:
    clean_news_only_report_final.json -> GIVEN TO THE MODEL (accepted news only)
    rejected_results_debug.json       -> developer only (rejected results + full report)
    scan_logs / articles tables       -> one row per scan, accepted news linked to it
    cost_impacts / alerts tables      -> refreshed after a successful scan (risk_alerts.py)
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from analyzer import CleanNewsOnlySupplyAnalyzer
from article_store import save_articles
from models import FinalCleanSupplyReport
from risk_alerts import update_risks
from scan_log import ScanFailed, scan_log

# All paths are relative to this file, so the scan works no matter
# which folder it is started from (e.g. by a scheduler or Task Scheduler)
HERE = Path(__file__).resolve().parent
SEARCH_PLAN_PATH = HERE / "search_plan.json"                  # produced by query_planner.py
OUTPUT_PATH = HERE / "clean_news_only_report_final.json"      # file given to the model
DEBUG_PATH = HERE / "rejected_results_debug.json"             # debug file, not given to the model

# Load TAVILY_API_KEY and POSTGRES_* from the .env file (keys are never written in the code)
load_dotenv(HERE / ".env")


def _write_atomic(path: Path, text: str) -> None:
    """Write to a temporary file first, then replace the target in one step.
    This way the model never reads a half-written JSON while a scan is running."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def run_scan(triggered_by: str = "manual") -> FinalCleanSupplyReport:
    """Run one full scan, write both JSON files and record it in scan_logs / articles.
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

    # The scan is now 'success': refresh cost_impacts / alerts / alert_articles for it.
    # News analysed by the agent after this point get their alerts with: python risk_alerts.py
    if scan.id is not None:
        try:
            update_risks(scan.id)
        except Exception as e:
            print(f"[!] Alert'ler güncellenemedi (tarama kaydedildi): {type(e).__name__}: {e}")
    return report


def main():
    # Runs started by cron / Task Scheduler pass --schedule; everything else is manual
    triggered_by = "schedule" if "--schedule" in sys.argv else "manual"
    try:
        run_scan(triggered_by)
    except ScanFailed as e:
        sys.exit(f"[!] Tarama başarısız: {e}")
    except (RuntimeError, FileNotFoundError) as e:
        sys.exit(f"[!] {e}")


if __name__ == "__main__":
    main()
