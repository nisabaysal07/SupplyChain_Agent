"""
Article Store Module:
Writes the news accepted in a scan to the articles table of supply_db.

Each article is upserted by URL:
    new URL      -> inserted with first_seen_scan_id = last_seen_scan_id = scan id
    known URL    -> last_seen_scan_id moves to this scan; if the text changed
                    (content_hash differs) title/content/hash/updated_at are refreshed

content_hash is computed the same way as db/data/03_haberler.sql:
sha256 of lower-cased "title content" with whitespace collapsed to single spaces.

Usage:
    article_ids = save_articles(scan.id, report)   # {url: articles.id}
"""
import hashlib
from typing import Dict, Optional

from models import FinalCleanSupplyReport, NewsSourceItem
from scan_log import connect


def content_hash(title: str, content: Optional[str]) -> str:
    text = " ".join(f"{title} {content or ''}".split()).lower()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


UPSERT_SQL = """
INSERT INTO articles (first_seen_scan_id, last_seen_scan_id, url, content_hash, title, content,
                      published_at, effective_date)
VALUES (%(scan_id)s, %(scan_id)s, %(url)s, %(hash)s, %(title)s, %(content)s,
        %(published)s, %(effective)s)
ON CONFLICT (url) DO UPDATE
   SET last_seen_scan_id = GREATEST(articles.last_seen_scan_id, EXCLUDED.last_seen_scan_id),
       published_at      = COALESCE(articles.published_at, EXCLUDED.published_at),
       effective_date    = COALESCE(EXCLUDED.effective_date, articles.effective_date),
       title             = CASE WHEN articles.content_hash <> EXCLUDED.content_hash
                                THEN EXCLUDED.title ELSE articles.title END,
       content           = CASE WHEN articles.content_hash <> EXCLUDED.content_hash
                                THEN EXCLUDED.content ELSE articles.content END,
       updated_at        = CASE WHEN articles.content_hash <> EXCLUDED.content_hash
                                THEN now() ELSE articles.updated_at END,
       content_hash      = EXCLUDED.content_hash
RETURNING id
"""


def _row(scan_id: int, news: NewsSourceItem) -> dict:
    # The scan keeps only the relevance summary of the text, so that is the stored content
    return {
        "scan_id": scan_id,
        "url": news.url,
        "hash": content_hash(news.title, news.summary),
        "title": news.title,
        "content": news.summary,
        "published": news.published_date,
        "effective": news.effective_date,
    }


def save_articles(scan_id: int, report: FinalCleanSupplyReport) -> Dict[str, int]:
    """Upsert every accepted news item of the report; return {url: articles.id}."""
    # The same article can be found by several queries in one scan
    unique = {news.url: news for rep in report.reports for news in rep.sources_found}
    if not unique:
        return {}

    ids = {}
    conn = connect()
    try:
        with conn.cursor() as cur:
            for url, news in unique.items():
                cur.execute(UPSERT_SQL, _row(scan_id, news))
                ids[url] = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    return ids
