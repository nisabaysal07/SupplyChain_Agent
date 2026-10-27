"""
Text Processing Utilities Module:
Provides functions for text normalization, term-boundary regex compilation, 
sentence splitting, noise/junk filtering, summary construction, and effective date extraction.
"""

import re
from typing import List, Optional

import config as cfg

# Regex patterns for cleaning unwanted characters, links, dates, and noise
_INVISIBLE = re.compile("[­​-‏⁠-⁤﻿]")  # Reuters'taki görünmez karakterler
_SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")
_ABBREV_END = re.compile(
    r"(?:\b(?:jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|no|mr|mrs|ms|dr|st|inc|co|ltd|corp|vs|gen|gov|sen|rep)|\bu\.s|\b[a-z])\.$",
    re.I,
)
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_BARE_URL = re.compile(r"https?://\S+")
_AGO = re.compile(r"\b\d+\s?(?:m|h|d|mins?|hours?|days?)\s+ago\b", re.I)
_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_EXPR = (
    rf"(?:{_MONTHS}\s+\d{{1,2}}(?:,?\s+\d{{4}})?|\d{{1,2}}\s+{_MONTHS}(?:\s+\d{{4}})?"
    r"|\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{4})"
)
_EFFECTIVE = re.compile(
    r"(?:effective(?:\s+from|\s+on|\s+as\s+of)?|take[sn]?\s+effect(?:\s+on|\s+from)?|enter(?:s|ed)?\s+into\s+force(?:\s+on)?"
    r"|in\s+force\s+from|starting(?:\s+from|\s+on)?|yürürlüğe\s+gir\w*)\s+(" + _DATE_EXPR + ")",
    re.I,
)


def normalize(text: Optional[str]) -> str:
    """Strip invisible characters and normalize whitespace."""
    text = _INVISIBLE.sub("", text or "")
    return re.sub(r"\s+", " ", text).strip()


def fold(text: Optional[str]) -> str:
    """Küçük harfe çevir (Türkçe 'İ' -> 'i' sorununu önleyerek)."""
    return normalize(text).replace("İ", "i").casefold()


def compile_terms(terms) -> Optional[re.Pattern]:
    """Compile a list of terms into a word-bounded regex pattern supporting prefix wildcards (*)."""
    parts = []
    for t in sorted({fold(x) for x in terms if x}, key=len, reverse=True):
        if t.endswith("*"):
            parts.append(re.escape(t[:-1]) + r"\w*")
        else:
            parts.append(re.escape(t) + r"(?:s|es|ed|d|ing)?")
    if not parts:
        return None
    return re.compile(r"(?<!\w)(?:" + "|".join(parts) + r")(?!\w)")


def has(pattern: Optional[re.Pattern], text_folded: str) -> bool:
    return bool(pattern and pattern.search(text_folded))


# Pre-compiled regex patterns generated from config terms
DISRUPTION_PAT = compile_terms(cfg.DISRUPTION_TERMS)
SEVERE_PAT = compile_terms(cfg.SEVERE_COUNTRY_EVENT_TERMS)
TRADE_PAT = compile_terms(cfg.TRADE_TERMS)
RESTRICTION_PAT = compile_terms(cfg.RESTRICTION_TERMS)
SECTOR_PAT = compile_terms(cfg.SECTOR_TERMS + [t for ts in cfg.PRODUCT_TERMS.values() for t in ts])
NOISE_TITLE_PAT = compile_terms(cfg.NOISE_TITLE_TERMS)
COMMODITY_TITLE_PAT = compile_terms(cfg.COMMODITY_TITLE_TERMS)
COUNTRY_PATS = {c: compile_terms(a) for c, a in cfg.COUNTRY_ALIASES.items()}


def split_sentences(text: str) -> List[str]:
    """Split text into sentences while preserving common abbreviations (e.g., 'U.S.', 'Nov.')."""
    out: List[str] = []
    for part in _SENT_SPLIT.split(text):
        if out and _ABBREV_END.search(out[-1]):
            out[-1] = out[-1] + " " + part
        else:
            out.append(part)
    return out


def is_junk_sentence(s: str) -> bool:
    sl = fold(s)
    words = s.split()
    if len(s) < 30 or len(words) < 5 or len(words) > 90:
        return True
    if any(j in sl for j in cfg.JUNK_PHRASES) or _AGO.search(s):
        return True
    alpha = [w for w in words if w[:1].isalpha()]
    if len(alpha) >= 8:
        upper_ratio = sum(1 for w in alpha if w[0].isupper()) / len(alpha)
        if upper_ratio > 0.6:  # menü / başlık listesi
            return True
    return False


def extract_sentences(*texts: str) -> List[str]:
    """Extract, clean, and deduplicate valid sentences from raw text input."""
    out, seen = [], set()
    for text in texts:
        if not text:
            continue
        text = text[: cfg.MAX_TEXT_CHARS]
        text = _MD_IMAGE.sub(" ", text)
        text = _MD_LINK.sub(r"\1", text)
        text = _BARE_URL.sub(" ", text)
        lines = []
        for line in text.splitlines():
            line = re.sub(r"^[\s#>*\-•|]+", "", line).strip()
            if len(line.split()) >= 5:      
                lines.append(line)
        for s in split_sentences(normalize(" ".join(lines))):
            s = s.strip()
            key = fold(s)
            if key in seen or is_junk_sentence(s):
                continue
            seen.add(key)
            out.append(s)
    return out


def with_context(hits: List[str], sentences: List[str]) -> List[str]:
    """Include adjacent sentences following matched hits to preserve critical event context."""
    idx = {s: i for i, s in enumerate(sentences)}
    keep = set()
    for h in hits:
        i = idx.get(h)
        if i is None:
            continue
        keep.add(i)
        nxt = sentences[i + 1] if i + 1 < len(sentences) else None
        
        if nxt and len(nxt.split()) <= 40 and any(
            has(p, fold(nxt)) for p in (TRADE_PAT, DISRUPTION_PAT, SECTOR_PAT)
        ):
            keep.add(i + 1)
    return [sentences[i] for i in sorted(keep)] or hits


def build_summary(hits: List[str]) -> str:
    out, total = [], 0
    for s in hits[: cfg.MAX_SUMMARY_SENTENCES]:
        if total + len(s) > cfg.MAX_SUMMARY_CHARS and out:
            break
        out.append(s)
        total += len(s) + 1
    return " ".join(out)


def extract_effective_date(text: str) -> Optional[str]:
    m = _EFFECTIVE.search(normalize(text))
    return m.group(1) if m else None