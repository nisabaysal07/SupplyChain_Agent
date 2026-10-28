"""
Scan Scheduler Module:
Runs the supply chain news scan immediately on start, then at the interval set in the panel
(Ayarlar → Haber tarama sıklığı, app_settings.scan_interval_hours; read again after every scan)
or every --interval hours.
Keeps running until it is stopped with Ctrl+C. A failed scan is logged and the scheduler
continues with the next run (one bad run never stops the schedule).

"""
import argparse
import time
import traceback
from datetime import datetime, timedelta

from main import run_scan
from models import FinalCleanSupplyReport
from scan_log import DEFAULT_SCAN_INTERVAL_HOURS, connect, scan_interval_hours


def on_scan_complete(report: FinalCleanSupplyReport) -> None:
    """Hook called after every successful scan (run_scan already saved it to scan_logs / articles).
    TODO (next step): send notifications for queries whose status is "Events Found"."""
    pass


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_interval(fixed: float = None) -> float:
    """--interval if given, else the panel setting (the default when the database is unreachable)."""
    if fixed:
        return fixed
    try:
        conn = connect()
    except Exception:
        return DEFAULT_SCAN_INTERVAL_HOURS
    try:
        return scan_interval_hours(conn)
    finally:
        conn.close()


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
    parser.add_argument("--interval", type=float, default=None,
                        help="Hours between scans (default: the panel setting, "
                             f"{DEFAULT_SCAN_INTERVAL_HOURS} if it is not set)")
    parser.add_argument("--no-initial", action="store_true",
                        help="Do not scan immediately on start; wait one interval first")
    args = parser.parse_args()

    hours = current_interval(args.interval)
    source = "--interval" if args.interval else "panel ayarı"
    print(f"[{_now()}] Zamanlayıcı başladı: her {hours:g} saatte bir tarama ({source}; durdurmak için Ctrl+C).")

    # Fixed-rate schedule: runs at start, start+3h, start+6h ... (a long scan does not shift the times)
    next_run = datetime.now() if not args.no_initial else datetime.now() + timedelta(hours=hours)
    try:
        while True:
            wait = (next_run - datetime.now()).total_seconds()
            if wait > 0:
                print(f"[{_now()}] Sonraki tarama: {next_run:%Y-%m-%d %H:%M}")
                time.sleep(wait)
            run_once()
            # A changed panel setting applies from the next scan on
            interval = timedelta(hours=current_interval(args.interval))
            next_run += interval
            # If a scan took longer than the interval, skip missed slots instead of running back-to-back
            while next_run <= datetime.now():
                next_run += interval
    except KeyboardInterrupt:
        print(f"\n[{_now()}] Zamanlayıcı durduruldu.")


if __name__ == "__main__":
    main()