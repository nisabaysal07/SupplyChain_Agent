"""
Main Entry Point Module:
Loads environment variables, validates configuration files, initializes
the supply chain analyzer, executes the scan, and exports final reports and debug logs.

Outputs:
    clean_news_only_report_final.json -> GIVEN TO THE MODEL (accepted news only)
    rejected_results_debug.json       -> developer only (rejected results + full report)
"""
import os
import sys

from dotenv import load_dotenv

from analyzer import CleanNewsOnlySupplyAnalyzer
load_dotenv()


def main():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        sys.exit("[!] TAVILY_API_KEY tanımlı değil (.env dosyasını kontrol edin).")

    search_plan_path = "search_plan.json"                
    output_path = "clean_news_only_report_final.json"    
    debug_path = "rejected_results_debug.json"           

    if not os.path.exists(search_plan_path):
        sys.exit(f"[!] Hata: {search_plan_path} bulunamadı.")

    # Initialize the supply chain analyzer instance
    analyzer = CleanNewsOnlySupplyAnalyzer(
        tavily_api_key=api_key,
        search_plan_path=search_plan_path,
        company_country="Turkey",
    )

    # Run all queries in the search plan
    report = analyzer.execute_scan()

    # Write the model file (trimmed fields) and the debug file (rejections + full report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(analyzer.export_to_json(report))
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(analyzer.export_rejections(report))

    # Summarize execution statistics and results
    found = sum(1 for r in report.reports if r.status == "Events Found")
    errors = sum(1 for r in report.reports if r.status == "Search Error")
    print(f"[✓] {len(report.reports)} sorgu | {found} sorguda haber | {errors} arama hatası "
          f"| {len(analyzer.rejections)} sonuç elendi")
    print(f"    Model için rapor: {output_path} | Elenenler (debug): {debug_path}")


if __name__ == "__main__":
    main()