"""
Main Entry Point Module:
Loads environment variables, validates configuration files, initializes
the supply chain analyzer, executes the scan, and exports final reports and debug logs.

"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from analyzer import CleanNewsOnlySupplyAnalyzer
from models import FinalCleanSupplyReport

# All paths are relative to this file, so the scan works no matter
# which folder it is started from (e.g. by a scheduler or Task Scheduler)
HERE = Path(__file__).resolve().parent
SEARCH_PLAN_PATH = HERE / "search_plan.json"                  # produced by query_planner.py
OUTPUT_PATH = HERE / "clean_news_only_report_final.json"      # file given to the model
DEBUG_PATH = HERE / "rejected_results_debug.json"             # debug file, not given to the model

# Load TAVILY_API_KEY from the .env file (the key is never written in the code)
load_dotenv(HERE / ".env")


def _write_atomic(path: Path, text: str) -> None:
    """Write to a temporary file first, then replace the target in one step.
    This way the model never reads a half-written JSON while a scan is running."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def run_scan() -> FinalCleanSupplyReport:
    """Run one full scan and write both JSON files.
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

    # Run all queries in the search plan
    report = analyzer.execute_scan()

    # Write the model file (trimmed fields) and the debug file (rejections + full report)
    _write_atomic(OUTPUT_PATH, analyzer.export_to_json(report))
    _write_atomic(DEBUG_PATH, analyzer.export_rejections(report))

    # Summarize execution statistics and results
    found = sum(1 for r in report.reports if r.status == "Events Found")
    errors = sum(1 for r in report.reports if r.status == "Search Error")
    print(f"[✓] {len(report.reports)} sorgu | {found} sorguda haber | {errors} arama hatası "
          f"| {len(analyzer.rejections)} sonuç elendi")
    print(f"    Model için rapor: {OUTPUT_PATH.name} | Elenenler (debug): {DEBUG_PATH.name}")
    return report


def main():
    try:
        run_scan()
    except (RuntimeError, FileNotFoundError) as e:
        sys.exit(f"[!] {e}")


if __name__ == "__main__":
    main()