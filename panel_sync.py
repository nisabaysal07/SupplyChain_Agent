"""
Panel Sync Module:
Sends the alerts of a scan to the web panel as events, so they appear on the Olaylar page, enter the
supplier risk scores and ring the notification bell (tedarikci_paneli/web/MODEL_ENTEGRASYONU.md).

Flow:  scan → agent → risk_alerts.py (alerts) → THIS → POST /api/model/olaylar
    Every alert is one panel event with the id 'alarm-<alerts.id>'; the same id replaces the event.
    Alerts with panel_synced_at IS NULL are sent, then panel_synced_at is set. risk_alerts.py clears
    panel_synced_at when an alert changes or is resolved, so:
        new       → new event                   → bell: "New article"
        changed   → same event, newer insight   → bell: "Model insight"
        resolved  → same event with an end date → leaves the risk scores, no bell
    The panel decides who gets a notification (Ayarlar → Bildirim tercihleri).

Settings from .env:
    PANEL_URL=http://localhost:3000
    NUXT_MODEL_API_TOKEN=...          # the same key the panel checks
Without the token, or while the panel is not running, nothing is sent and the alerts stay pending.

Usage:
    python panel_sync.py              # send the pending alerts now
    python panel_sync.py --dry-run    # print the events, send nothing
    python panel_sync.py --all        # send every alert again (e.g. after the panel data was reset);
                                      # active alerts that changed since their last sync ring the bell again
main.run_scan calls sync_panel() after every successful scan.
"""
import argparse
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from notify import EVENT_LABELS
from risk_alerts import ADD_PANEL_COLUMN_SQL
from scan_log import connect

HERE = Path(__file__).resolve().parent
TIMEOUT = 15

# The panel matches events to suppliers by these names (see web/server/utils/veri.ts)
PENDING_SQL = """
SELECT al.id, al.event_type, al.status, al.severity, al.current_score, al.change_reason, al.updated_at,
       al.created_at, al.last_seen_scan_id, al.resolved_scan_id IS NOT NULL AS resolved,
       s.name AS firma, i.hs6, l.name AS nokta, c.name_tr AS ulke,
       COALESCE(s.name, i.name, l.name, c.name_tr) AS target,
       aa.summary, aa.old_rate_pct, aa.new_rate_pct, aa.price_change_pct, aa.expected_delay_days,
       ar.title, ar.url, ar.published_at, ci.message,
       ARRAY(SELECT si.id FROM supplier_items si
             WHERE si.supplier_id = al.supplier_id OR si.item_id = al.item_id ORDER BY si.id) AS tedarikci_idleri,
       ARRAY(SELECT a2.url FROM alert_articles x JOIN articles a2 ON a2.id = x.article_id
             WHERE x.alert_id = al.id ORDER BY x.added_scan_id, a2.id) AS kaynaklar
FROM alerts al
LEFT JOIN suppliers s ON s.id = al.supplier_id
LEFT JOIN items i     ON i.id = al.item_id
LEFT JOIN locations l ON l.id = al.location_id
LEFT JOIN countries c ON c.id = al.country_id
LEFT JOIN article_analyses aa ON aa.id = al.latest_analysis_id
LEFT JOIN articles ar         ON ar.id = aa.article_id
LEFT JOIN cost_impacts ci     ON ci.article_analysis_id = al.latest_analysis_id
WHERE al.panel_synced_at IS NULL OR %(all)s
ORDER BY al.id
"""
MARK_SYNCED_SQL = "UPDATE alerts SET panel_synced_at = now() WHERE id = ANY(%s)"

PANEL_TYPES = {
    "tariff_increase": "vergi",
    "tariff_decrease": "vergi",
    "trade_restriction": "jeopolitik",
    "transport_disruption": "liman",
    "price_change": "fiyat",
    "other": "jeopolitik",
}
LEVELS = {"low": "dusuk", "medium": "orta", "high": "yuksek"}
DELAY_TYPES = ("transport_disruption", "trade_restriction")


def _text(text: Optional[str], limit: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit - 1].rsplit(" ", 1)[0] + "…"


def _https(url: Optional[str]) -> Optional[str]:
    return url if url and url.startswith("https://") and " " not in url and len(url) <= 2000 else None


def _extra_cost(a: dict) -> Optional[float]:
    """Extra cost rate the panel multiplies with the yearly purchase (0.10 = 10%); only increases."""
    if a["event_type"] == "tariff_increase" and a["old_rate_pct"] is not None and a["new_rate_pct"] is not None:
        rate = float(a["new_rate_pct"]) - float(a["old_rate_pct"])
    elif a["event_type"] == "price_change" and a["price_change_pct"] is not None:
        rate = float(a["price_change_pct"])
    else:
        return None
    return round(min(rate / 100, 5), 4) if rate > 0 else None


def build_event(a: dict, today: date) -> Optional[dict]:
    """The panel event of one alert, or None when the panel could not match it to any supplier."""
    kapsam = {k: [v] for k, v in (("firmalar", a["firma"]), ("hs6", a["hs6"]), ("noktalar", a["nokta"]),
                                  ("ulkeler", a["ulke"])) if v}
    if not kapsam:
        return None
    label = EVENT_LABELS.get(a["event_type"], "Supply risk")
    # The panel only shows and notifies events that have started, so the news date is the start
    start = min((a["published_at"] or a["created_at"]).date(), today)
    # A resolved risk ends yesterday: it leaves the risk scores today and stays in the history
    end = max(start, today - timedelta(days=1)) if a["resolved"] else None
    url = _https(a["url"])
    findings = []
    if a["message"]:
        # The bell shows the first finding's title, so it carries the result itself ("Annual $39,600, ...")
        findings.append({"baslik": _text(a["message"].split(". ")[0], 200), "aciklama": _text(a["message"], 3000),
                         "seviye": LEVELS[a["severity"]], "tedarikciIdleri": a["tedarikci_idleri"][:100]})
    if a["status"] == "changed" and a["change_reason"]:
        findings.append({"baslik": "What changed", "aciklama": _text(a["change_reason"], 3000),
                         "seviye": LEVELS[a["severity"]]})
    sources = [u for u in dict.fromkeys(_https(u) for u in a["kaynaklar"]) if u][:50]

    event = {
        "id": f"alarm-{a['id']}",
        "baslik": _text(a["title"] or f"{label}: {a['target']}", 200),
        "ozet": _text(a["summary"] or a["title"] or label, 2000),
        "tur": PANEL_TYPES.get(a["event_type"], "jeopolitik"),
        "siddet": LEVELS[a["severity"]],
        "tarih": start.isoformat(),
        "bitisTarihi": end.isoformat() if end else None,
        "kaynak": {"ad": _text(urlparse(url).hostname if url else "ChainGuard scan", 200), "url": url},
        "kapsam": kapsam,
        "gecikmeVar": a["event_type"] in DELAY_TYPES or bool(a["expected_delay_days"]),
        # The insight changes only when the alert does: the panel rings the bell again for a newer one
        "cikarim": {
            "baslik": _text(f"{label}: {a['target']}", 200),
            "olusturma": a["updated_at"].isoformat(),
            "model": {"ad": "ChainGuard", "surum": f"scan {a['last_seen_scan_id']}"},
            "ozet": _text(a["summary"] or a["title"] or label, 5000),
            "genelDegerlendirme": {"seviye": LEVELS[a["severity"]],
                                   **({"skor": a["current_score"]} if a["current_score"] else {})},
            "bulgular": findings,
            "kaynaklar": [{"ad": _text(urlparse(u).hostname, 200), "url": u} for u in sources],
        },
    }
    extra = _extra_cost(a)
    if extra:
        event["ekMaliyetOrani"] = extra
    return event


def post_event(session: requests.Session, panel: str, event: dict) -> bool:
    try:
        r = session.post(f"{panel}/api/model/olaylar", json=event, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise ConnectionError(f"panele ulaşılamadı ({panel}): {type(e).__name__}") from e
    if r.status_code in (200, 201):
        warnings = r.json().get("uyarilar") or []
        for w in warnings:
            print(f"[!] {event['id']}: {w}")
        return True
    if r.status_code in (401, 503):
        raise PermissionError(f"panel erişim anahtarını kabul etmedi (HTTP {r.status_code}, NUXT_MODEL_API_TOKEN)")
    print(f"[!] {event['id']} reddedildi (HTTP {r.status_code}): {r.text[:300]}")
    return False


def sync_panel(dry_run: bool = False, resend_all: bool = False) -> int:
    """Sends the pending alerts to the panel and marks them as synced. Returns how many were sent."""
    panel = os.getenv("PANEL_URL", "http://localhost:3000").rstrip("/")
    token = os.getenv("NUXT_MODEL_API_TOKEN", "").strip()
    if not token and not dry_run:
        print("[i] Panele gönderilmedi: NUXT_MODEL_API_TOKEN tanımlı değil")
        return 0

    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(ADD_PANEL_COLUMN_SQL)
            cur.execute(PENDING_SQL, {"all": resend_all})
            cols = [d[0] for d in cur.description]
            alerts = [dict(zip(cols, r)) for r in cur.fetchall()]
        conn.commit()
        if not alerts:
            print("[✓] Panele gönderilecek yeni alarm yok")
            return 0

        today = date.today()
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {token}"
        synced, sent = [], 0
        try:
            for a in alerts:
                event = build_event(a, today)
                if event is None:
                    print(f"[!] Alarm {a['id']}: hedefi panelde eşleşmiyor, atlandı")
                    synced.append(a["id"])   # nothing to retry until the alert changes
                elif dry_run:
                    print(json.dumps(event, ensure_ascii=False, indent=2, default=str))
                elif post_event(session, panel, event):
                    synced.append(a["id"])
                    sent += 1
        except (ConnectionError, PermissionError) as e:
            # The rest stay pending and are sent on the next run
            print(f"[!] Panel senkronu durdu: {e}")
        if dry_run:
            return 0
        with conn.cursor() as cur:
            cur.execute(MARK_SYNCED_SQL, (synced,))
        conn.commit()
        print(f"[✓] {sent}/{len(alerts)} alarm panele gönderildi")
        return sent
    finally:
        conn.close()


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Send the alerts to the web panel as events")
    parser.add_argument("--dry-run", action="store_true", help="Print the events, send nothing")
    parser.add_argument("--all", action="store_true", help="Send every alert again, not only the pending ones")
    args = parser.parse_args(argv)
    load_dotenv(HERE / ".env")
    sync_panel(dry_run=args.dry_run, resend_all=args.all)


if __name__ == "__main__":
    main()
