"""
Scan Log Module:
Records every news scan in the scan_logs table of supply_db.

A row is opened as 'running' when the scan starts and closed as 'success' or
'failed' (with the error message) when it ends. The returned scan id is what
articles.first_seen_scan_id / last_seen_scan_id will point to.

Usage:
    with scan_log("manual") as scan_id:
        ...run the scan...

If the database cannot be reached the scan still runs; scan_id is then None.
"""
import os
from contextlib import contextmanager

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


def finish_scan(conn, scan_id: int, status: str, error_message: str | None = None) -> None:
    """Close the row as 'success' or 'failed'."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE scan_logs SET status = %s, finished_at = now(), error_message = %s WHERE id = %s",
            (status, error_message, scan_id),
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
        scan_id = start_scan(conn, triggered_by)
    except (psycopg2.Error, KeyError) as e:
        print(f"[!] scan_logs'a yazılamadı, tarama loglanmadan devam ediyor: {e}")
        yield None
        return

    print(f"[i] Tarama başladı (scan_logs.id = {scan_id})")
    try:
        yield scan_id
    except BaseException as e:
        # KeyboardInterrupt (Ctrl+C) too, so no row is left stuck at 'running'
        finish_scan(conn, scan_id, "failed", f"{type(e).__name__}: {e}"[:2000])
        print(f"[✗] Tarama başarısız (scan_logs.id = {scan_id})")
        raise
    else:
        finish_scan(conn, scan_id, "success")
        print(f"[✓] Tarama scan_logs'a kaydedildi (scan_logs.id = {scan_id})")
    finally:
        conn.close()
