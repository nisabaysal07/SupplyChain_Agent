"""Impact score (0-100) and the is_relevant flag.

The score is computed in code, not by the model, so the same facts always give the same
score. It has two parts:

1. Certainty sets the band. In force or ongoing: 80-100; proposed: 66-79; unclear: 61-65;
   not relevant: 10. A reader can tell the status from the band alone.
2. Size sets the place inside the band, from 0 to 20 points:
   - suppliers: 2 points per affected supplier, at most 10
   - event: tariff or tax increase, half a point per percentage point of increase;
     transport disruption, 10 points for a delay of 14 days or more, less for shorter;
     trade restriction, 5 points; price increase, a quarter point per percent; at most 10.
   Only what is bad for us counts: a duty cut or a price drop stays at the bottom of its band,
   and so does a VAT change, which does not change our cost (VAT is deductible). A value the
   article does not state adds nothing.

An article is relevant when its score is above THRESHOLD.
"""

from __future__ import annotations

BANDS = {
    "enacted": (80, 100),        # decided measure or price change that happened
    "ongoing_event": (80, 100),  # disruption happening now
    "proposed": (66, 79),        # draft or plan
    "unclear": (61, 65),         # the article does not say
}
DIRECT_NO_ANALYSIS = 65   # analysis failed: kept above the threshold so the alert is not lost
NONE_SCORE = 10
THRESHOLD = 60

MAX_POINTS = 20
DELAY_FULL_DAYS = 14
RESTRICTION_POINTS = 5


def is_relevant(score: int | None) -> bool | None:
    return None if score is None else score > THRESHOLD


def _event_points(event_type: str | None, a: dict) -> float | None:
    """Points for the size of the event; None when the event is good news for us."""
    if event_type == "tariff_decrease":
        return None
    if event_type == "tariff_increase":
        if a.get("rate_type") == "kdv" or a.get("new_rate_pct") is None:
            return 0
        return max(0.0, (a["new_rate_pct"] - (a.get("old_rate_pct") or 0)) / 2)
    if event_type == "transport_disruption":
        days = a.get("expected_delay_days")
        return 10 * min(days, DELAY_FULL_DAYS) / DELAY_FULL_DAYS if days else 0
    if event_type == "trade_restriction":
        return RESTRICTION_POINTS
    if event_type == "price_change":
        pct = a.get("price_change_pct")
        if pct is not None and pct < 0:
            return None
        return pct / 4 if pct else 0
    return 0


def size_points(event_type: str | None, analysis: dict, n_suppliers: int) -> float:
    """0-20 points: how big the event is for us."""
    event = _event_points(event_type, analysis)
    if event is None:
        return 0
    return min(2 * n_suppliers, 10) + min(event, 10)


def impact_score(impact_level: str | None, analysis: dict | None = None,
                 event_type: str | None = None, n_suppliers: int = 0) -> int | None:
    """None when the filter failed for this article (it will be processed again)."""
    if impact_level is None:
        return None
    if impact_level != "direct":
        return NONE_SCORE
    band = BANDS.get((analysis or {}).get("status"))
    if band is None:
        return DIRECT_NO_ANALYSIS
    low, high = band
    points = size_points(event_type, analysis, n_suppliers)
    return low + round(points / MAX_POINTS * (high - low))
