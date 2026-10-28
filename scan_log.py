"""
Scan Log Module:
Records every news scan in the scan_logs table of supply_db.

A row is opened as 'running' when the scan starts and closed as 'success' or
'failed' (with the error message) when it ends, together with the scan summary
counts (queries run, news found, results rejected, queries with search errors).
scan.id is what articles.first_seen_scan_id / last_seen_scan_id will point to.

Usage:
    with scan_log("manual") as scan:
        ...run the scan...
        scan.set_counts(query_count=28, found_count=5, rejected_count=230, error_count=0)

If the database cannot be reached the scan still runs; scan.id is then None.
"""
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

import psycopg2


def connect():
    """Connect with the same POSTGRES_* variables db/*.py scripts use."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


@dataclass
class ScanRun:
    """The scan in progress: its scan_logs id and the summary counts to write at the end."""
    id: Optional[int]
    query_count: Optional[int] = None
    found_count: Optional[int] = None
    rejected_count: Optional[int] = None
    error_count: Optional[int] = None

    def set_counts(self, query_count: int, found_count: int, rejected_count: int, error_count: int) -> None:
        self.query_count = query_count
        self.found_count = found_count
        self.rejected_count = rejected_count
        self.error_count = error_count


def start_scan(conn, triggered_by: str) -> int:
    """Insert a 'running' row and return its id."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO scan_logs (triggered_by, status) VALUES (%s, 'running') RETURNING id",
            (triggered_by,),
        )
        scan_id = cur.fetchone()[0]
    conn.commit()
    return scan_id


def finish_scan(conn, scan: ScanRun, status: str, error_message: Optional[str] = None) -> None:
    """Close the row as 'success' or 'failed' and write the counts (NULL if never set)."""
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE scan_logs
                  SET status = %s, finished_at = now(), error_message = %s,
                      query_count = %s, found_count = %s, rejected_count = %s, error_count = %s
                WHERE id = %s""",
            (status, error_message, scan.query_count, scan.found_count,
             scan.rejected_count, scan.error_count, scan.id),
        )
    conn.commit()


class ScanFailed(Exception):
    """Raise inside the block to mark the scan 'failed' without a traceback."""


@contextmanager
def scan_log(triggered_by: str = "manual"):
    if triggered_by not in ("schedule", "manual"):
        raise ValueError("triggered_by 'schedule' veya 'manual' olmalı")

    try:
        conn = connect()
        scan = ScanRun(id=start_scan(conn, triggered_by))
    except (psycopg2.Error, KeyError) as e:
        print(f"[!] scan_logs'a yazılamadı, tarama loglanmadan devam ediyor: {e}")
        yield ScanRun(id=None)
        return

    print(f"[i] Tarama başladı (scan_logs.id = {scan.id})")
    try:
        yield scan
    except BaseException as e:
        # KeyboardInterrupt (Ctrl+C) too, so no row is left stuck at 'running'
        finish_scan(conn, scan, "failed", f"{type(e).__name__}: {e}"[:2000])
        print(f"[✗] Tarama başarısız (scan_logs.id = {scan.id})")
        raise
    else:
        finish_scan(conn, scan, "success")
        print(f"[✓] Tarama scan_logs'a kaydedildi (scan_logs.id = {scan.id})")
    finally:
        conn.close()
