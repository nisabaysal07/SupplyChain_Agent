"""Loads news articles and the supplier list.

Articles come from one of two sources:
  - the project database (load_news_db): rows of the articles table that have no
    analysis yet (read only; results are stored by agent.save)
  - a JSON file (load_news) in the news collector's format, also used by the test set:
        {"reports": [{"status": ..., "sources_found": [
            {"news_id", "title", "published_date", "source_name", "url", "summary"}, ...]}]}
Both are converted to one internal format, so the rest of the agent does not depend on
where the articles come from.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _date_only(value) -> str | None:
    """'2026-10-12T08:30:00Z' -> '2026-10-12'; 'Tue, 20 Oct 2026 14:00:22 GMT' -> '2026-10-20'."""
    if not value:
        return None
    value = str(value).strip()
    m = re.match(r"\d{4}-\d{2}-\d{2}", value)
    if m:
        return m.group(0)
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return value


def _make_id(url: str, title: str) -> str:
    """Stable id for an article without one, so the same article always gets the same id."""
    return "U" + hashlib.sha1((url or title).encode("utf-8")).hexdigest()[:10]


def normalize(item: dict) -> dict:
    title = _clean(item.get("title"))
    url = item.get("url") or ""
    published = item.get("published_date")
    return {
        "id": str(item.get("news_id") or _make_id(url, title)),
        "title": title,
        "date": _date_only(published) or "",
        "full_text": _clean(item.get("summary")),
        "source_name": item.get("source_name"),
        "url": url or None,
        "published_at": published,
    }


def load_news(path: str | Path) -> tuple[list[dict], list[str]]:
    """Returns (articles, warnings). Duplicate articles are skipped."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not (isinstance(data, dict) and isinstance(data.get("reports"), list)):
        raise ValueError(f'{path}: expected {{"reports": [{{"sources_found": [...]}}]}}')
    raw = [n for grp in data["reports"] for n in (grp.get("sources_found") or [])]

    news, warnings, seen = [], [], set()
    for i, item in enumerate(raw):
        n = normalize(item)
        if not n["title"] and not n["full_text"]:
            warnings.append(f"record {i} skipped: no title or text")
            continue
        key = n["url"] or n["id"]
        if key in seen or n["id"] in seen:
            warnings.append(f"{n['id']} skipped: duplicate article")
            continue
        seen.update({key, n["id"]})
        if not n["full_text"]:
            warnings.append(f"{n['id']}: no text, judged on the title only")
        news.append(n)
    return news, warnings


# Articles that have no row in article_analyses yet
UNANALYSED_ARTICLES = """
SELECT a.id, a.title, a.content, a.url, a.published_at, a.last_seen_scan_id
FROM articles a
WHERE NOT EXISTS (SELECT 1 FROM article_analyses aa WHERE aa.article_id = a.id)
ORDER BY a.id
"""


def _source_from_url(url: str | None) -> str | None:
    """'https://www.reuters.com/world/...' -> 'reuters.com'."""
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else (host or None)


def connect():
    """Opens a connection to the project database.

    Settings come from the environment (.env): POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    and optionally POSTGRES_HOST (default localhost) and POSTGRES_PORT (5432).
    """
    import psycopg  # only needed in database mode

    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )


def load_news_db() -> tuple[list[dict], list[str]]:
    """Reads articles without an analysis from the project database (read only).

    Each article keeps its article_id and scan_log_id (the scan it was last seen in), so the
    results can be stored against the right rows.
    """
    with connect() as conn:
        rows = conn.execute(UNANALYSED_ARTICLES).fetchall()

    news, warnings = [], []
    for article_id, title, content, url, published_at, scan_id in rows:
        n = {
            "id": str(article_id),
            "title": _clean(title),
            "date": published_at.date().isoformat() if published_at else "",
            "full_text": _clean(content),
            "source_name": _source_from_url(url),
            "url": url,
            "published_at": published_at.isoformat() if published_at else None,
            "article_id": article_id,
            "scan_log_id": scan_id,
        }
        if not n["full_text"]:
            warnings.append(f"{n['id']}: no text, judged on the title only")
        news.append(n)
    return news, warnings


def load_suppliers(path: str | Path) -> tuple[list[dict], object]:
    """Supplier file: {"company": ..., "suppliers": [...]} (built by data/build_suppliers.py)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["suppliers"], data.get("company")
