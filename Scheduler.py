"""
Scan Scheduler Module:
Runs the supply chain news scan immediately on start, then every SCAN_INTERVAL_HOURS hours.
Keeps running until it is stopped with Ctrl+C. A failed scan is logged and the scheduler
continues with the next run (one bad run never stops the schedule).

"""
import argparse
import time
import traceback
from datetime import datetime, timedelta

from main import run_scan
from models import FinalCleanSupplyReport

SCAN_INTERVAL_HOURS = 3.0


def on_scan_complete(report: FinalCleanSupplyReport) -> None:
    """Hook called after every successful scan (run_scan already saved it to scan_logs / articles).
    TODO (next step): send notifications for queries whose status is "Events Found"."""
    pass


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_once() -> None:
    """Run a single scan; log errors instead of crashing the scheduler."""
    print(f"\n[{_now()}] Tarama başlıyor...")
    try:
        report = run_scan(triggered_by="schedule")
        on_scan_complete(report)
        print(f"[{_now()}] Tarama tamamlandı.")
    except Exception:
        print(f"[{_now()}] [!] Tarama başarısız, bir sonraki çalışmada tekrar denenecek:")
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Run the supply chain news scan on a fixed schedule.")
    parser.add_argument("--interval", type=float, default=SCAN_INTERVAL_HOURS,
                        help=f"Hours between scans (default: {SCAN_INTERVAL_HOURS})")
    parser.add_argument("--no-initial", action="store_true",
                        help="Do not scan immediately on start; wait one interval first")
    args = parser.parse_args()

    interval = timedelta(hours=args.interval)
    print(f"[{_now()}] Zamanlayıcı başladı: her {args.interval:g} saatte bir tarama (durdurmak için Ctrl+C).")

    # Fixed-rate schedule: runs at start, start+3h, start+6h ... (a long scan does not shift the times)
    next_run = datetime.now() if not args.no_initial else datetime.now() + interval
    try:
        while True:
            wait = (next_run - datetime.now()).total_seconds()
            if wait > 0:
                print(f"[{_now()}] Sonraki tarama: {next_run:%Y-%m-%d %H:%M}")
                time.sleep(wait)
            run_once()
            next_run += interval
            # If a scan took longer than the interval, skip missed slots instead of running back-to-back
            while next_run <= datetime.now():
                next_run += interval
    except KeyboardInterrupt:
        print(f"\n[{_now()}] Zamanlayıcı durduruldu.")


if __name__ == "__main__":
    main()