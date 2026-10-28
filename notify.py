"""
Notification Module (Görev 6.3):
Sends the important alerts of a scan to Slack, Teams, e-mail, Telegram, Discord ... through Apprise,
so the team hears about a risk even when the web panel is closed.

Flow:  scan → agent → risk_alerts.py (alerts) → THIS
    Alerts that are 'new' or 'changed', at least NOTIFY_MIN_SEVERITY and not notified yet are sent
    in one message (highest priority first), then alerts.notified_at is set. risk_alerts.py clears
    notified_at when an alert changes, so a risk is announced again only when something changed.

Channels come from .env (comma separated Apprise URLs, see https://github.com/caronc/apprise/wiki):
    NOTIFY_URLS=slack://TokenA/TokenB/TokenC, mailto://user:app-password@gmail.com
    NOTIFY_MIN_SEVERITY=high          # high (default) | medium | low
    PANEL_URL=http://localhost:3000   # link in the message
Without NOTIFY_URLS the message is only printed and the alerts stay unsent.

Usage:
    python notify.py --test           # sample alert, no database needed (checks the channels)
    python notify.py                  # send the pending alerts now
    python notify.py --dry-run        # show what would be sent, send nothing
main.run_scan calls send_alerts() after every successful scan.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import apprise
from dotenv import load_dotenv

from scan_log import connect

HERE = Path(__file__).resolve().parent
SEVERITIES = ("low", "medium", "high")
MAX_LISTED = 5   # alerts written out in one message; the rest are counted

EVENT_LABELS = {
    "tariff_increase": "Tariff increase",
    "tariff_decrease": "Tariff decrease",
    "trade_restriction": "Trade restriction",
    "transport_disruption": "Transport disruption",
    "price_change": "Price change",
    "other": "Supply risk",
}

PENDING_SQL = """
SELECT al.id, al.event_type, al.status, al.severity, al.current_score, al.change_reason,
       COALESCE(s.name, i.name, l.name, c.name_en) AS target,
       aa.summary, ar.title, ar.url, ci.message
FROM alerts al
LEFT JOIN suppliers s ON s.id = al.supplier_id
LEFT JOIN items i     ON i.id = al.item_id
LEFT JOIN locations l ON l.id = al.location_id
LEFT JOIN countries c ON c.id = al.country_id
LEFT JOIN article_analyses aa ON aa.id = al.latest_analysis_id
LEFT JOIN articles ar         ON ar.id = aa.article_id
LEFT JOIN cost_impacts ci     ON ci.article_analysis_id = al.latest_analysis_id
WHERE al.status IN ('new', 'changed') AND al.notified_at IS NULL AND al.severity = ANY(%s)
ORDER BY al.priority_score DESC NULLS LAST, al.id
"""
MARK_SENT_SQL = "UPDATE alerts SET notified_at = now() WHERE id = ANY(%s)"

# --test message: looks like a real alert, needs no database
SAMPLE_ALERT = {
    "id": 0, "event_type": "tariff_increase", "status": "new", "severity": "high", "current_score": 82,
    "change_reason": None, "target": "Cooler Master (CPU coolers)",
    "summary": "Turkey raises the additional customs duty on CPU coolers imported from China from 20% to 30%.",
    "title": "Additional duty on Chinese computer components raised", "url": "https://example.com/news",
    "message": "Yearly part cost +4.2% (≈ $318,000); +$2.10 per PC.",
}


def _min_severities() -> List[str]:
    level = os.getenv("NOTIFY_MIN_SEVERITY", "high").strip().lower()
    return list(SEVERITIES[SEVERITIES.index(level if level in SEVERITIES else "high"):])


def _group(alerts: List[dict]) -> List[dict]:
    """Alerts from the same article and event (e.g. one tariff hitting three suppliers) become one
    block naming every target, so the message does not repeat the same news."""
    groups = {}
    for a in alerts:
        g = groups.setdefault((a["event_type"], a.get("url") or a["id"]), {**a, "targets": []})
        if a["target"] and a["target"] not in g["targets"]:
            g["targets"].append(a["target"])
    return list(groups.values())


def _short(text: str, limit: int = 320) -> str:
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def _alert_block(a: dict) -> str:
    label = EVENT_LABELS.get(a["event_type"], "Supply risk")
    lines = [f"**[{a['severity'].upper()}] {label} – {', '.join(a['targets']) or 'unknown target'}**"
             + (" (updated)" if a["status"] == "changed" else "")]
    if a.get("summary"):
        lines.append(_short(a["summary"]))
    if a.get("message"):
        lines.append(f"Impact: {a['message']}")
    if a["status"] == "changed" and a.get("change_reason"):
        lines.append(f"What changed: {a['change_reason']}")
    if a.get("url"):
        lines.append(f"Source: [{a.get('title') or a['url']}]({a['url']})")
    lines.append(f"Impact score: {a['current_score']}/100")
    return "\n".join(lines)


def build_message(alerts: List[dict]) -> tuple:
    """(title, body) of one message for all alerts."""
    high = sum(a["severity"] == "high" for a in alerts)
    title = f"ChainGuard: {len(alerts)} supply chain risk{'s' if len(alerts) > 1 else ''}"
    if high:
        title += f" ({high} high)"
    groups = _group(alerts)   # alerts arrive highest priority first, so do the groups
    blocks = [_alert_block(g) for g in groups[:MAX_LISTED]]
    if len(groups) > MAX_LISTED:
        blocks.append(f"…and {len(groups) - MAX_LISTED} more.")
    panel = os.getenv("PANEL_URL", "http://localhost:3000").rstrip("/")
    blocks.append(f"Open the dashboard: {panel}/olaylar")
    return title, "\n\n".join(blocks)


def send(title: str, body: str, high: bool, dry_run: bool = False) -> bool:
    """Sends to every NOTIFY_URLS channel. True only if a channel accepted it."""
    urls = [u.strip() for u in os.getenv("NOTIFY_URLS", "").split(",") if u.strip()]
    if dry_run or not urls:
        why = "deneme (--dry-run)" if dry_run else "NOTIFY_URLS tanımlı değil"
        print(f"[i] Bildirim gönderilmedi ({why}):\n--- {title} ---\n{body}\n---")
        return False
    # One Apprise per channel: Apprise.notify is False when any channel fails, but a channel that cannot
    # work right now (windows:// with no desktop session) must not keep the alerts pending for Slack too
    sent = 0
    for url in urls:
        scheme = url.split("://")[0]
        ap = apprise.Apprise()
        if not ap.add(url):
            print(f"[!] Geçersiz bildirim adresi atlandı: {scheme}://...")
            continue
        if ap.notify(title=title, body=body, body_format=apprise.NotifyFormat.MARKDOWN,
                     notify_type=apprise.NotifyType.FAILURE if high else apprise.NotifyType.WARNING):
            sent += 1
        else:
            print(f"[!] Bildirim gönderilemedi: {scheme}://...")
    print(f"[✓] Bildirim gönderildi ({sent}/{len(urls)} kanal)" if sent else "[!] Bildirim hiçbir kanala gönderilemedi")
    return sent > 0


def send_alerts(dry_run: bool = False) -> int:
    """Sends the pending alerts in one message and marks them as notified. Returns how many were sent."""
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(PENDING_SQL, (_min_severities(),))
            cols = [d[0] for d in cur.description]
            alerts = [dict(zip(cols, r)) for r in cur.fetchall()]
        if not alerts:
            print("[✓] Bildirilecek yeni alarm yok")
            return 0
        title, body = build_message(alerts)
        if not send(title, body, any(a["severity"] == "high" for a in alerts), dry_run):
            return 0   # stay pending, sent on the next run
        with conn.cursor() as cur:
            cur.execute(MARK_SENT_SQL, ([a["id"] for a in alerts],))
        conn.commit()
        return len(alerts)
    finally:
        conn.close()


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Send the important alerts to Slack / Teams / e-mail ... (Apprise)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--test", action="store_true", help="Send a sample alert (no database needed)")
    group.add_argument("--dry-run", action="store_true", help="Show the pending alerts, send nothing")
    args = parser.parse_args(argv)
    load_dotenv(HERE / ".env")

    if args.test:
        title, body = build_message([SAMPLE_ALERT])
        if not send("[TEST] " + title, body, high=True):
            sys.exit(1)
        return
    send_alerts(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
