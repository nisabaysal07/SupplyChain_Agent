# Agent output format (version 1.3)

The agent writes one JSON file per run. The cost module, the database and the user interface
read this file. `python -m agent --db --save` also writes the rows described under
"Database mapping"; a results file can be stored later with `python -m agent.save <file>`.
Articles with `errors` are not stored, so the next run analyses them again.

The agent extracts facts from the news (suppliers, rates, dates, status); it does not compute
costs or risks. A value the article does not state is `null`; the model does not guess.
Supplier ids always come from the supplier list: an id the model invents is removed and
recorded in `warnings`.

## File structure

```json
{
  "schema_version": "1.3",
  "run": { ... run information ... },
  "results": [ { ... article 1 ... }, { ... article 2 ... } ]
}
```

## `results`: one record per article

Example (a decided tariff increase):

```json
{
  "news_id": "N01",
  "title": "Çin menşeli bilgisayar aksamına yüzde 20 ilave gümrük vergisi",
  "source_name": "Resmî Gazete",
  "source_url": "https://...",
  "published_at": "2026-10-14",

  "impact_level": "direct",
  "impact_score": 96,
  "is_relevant": true,
  "affected_supplier_ids": ["2", "5", "7"],
  "event_type": "tariff_increase",
  "filter_reason": "Turkey raised the duty on Chinese HS 8473.30 parts, which suppliers 2, 5 and 7 supply.",

  "analysis": {
    "affected_suppliers": [{"supplier_id": "5", "why": "ASUS graphics cards are of Chinese origin, HS 8473.30."}],
    "event_type": "tariff_increase",
    "status": "enacted",
    "country": "China",
    "affected_locations": [],
    "rate_type": "igv",
    "old_rate_pct": 0,
    "new_rate_pct": 20,
    "effective_date": "2026-11-15",
    "expected_delay_days": null,
    "summary": "Turkey raised the additional customs duty on Chinese-origin computer parts under HS 8473.30 from 0% to 20%, effective 15 November 2026...",
    "evidence_quote": "ilave gümrük vergisi yüzde 0'dan yüzde 20'ye çıkarıldı"
  },

  "warnings": [],
  "errors": []
}
```

### Article fields (copied from the source)

| Field | Type | Description |
|---|---|---|
| `news_id` | string | Article id. In database mode this is `articles.id`; from a JSON file it is the file's `news_id` (or a stable id derived from the URL) |
| `article_id`, `scan_log_id` | int | **Database mode only**: `articles.id` and the scan the article was last seen in (`articles.last_seen_scan_id`) |
| `title`, `source_name`, `source_url` | string | Title, source, link |
| `published_at` | string / null | Publication date as given in the news file |

### Filter result (Nemotron 3 Super)

| Field | Type | Description |
|---|---|---|
| `impact_level` | `"direct"` / `"none"` / `null` | **direct** = relevant (alert). **none** = not relevant. **null** = the filter failed for this article (see `errors`) |
| `impact_score` | int 0–100 / `null` | Computed in code (`agent/scoring.py`), see "Impact score" below. The band shows the status: **80–100** in force or ongoing, **66–79** proposed, **61–65** unclear (65 also when the analysis failed), **10** not relevant |
| `is_relevant` | `true` / `false` / `null` | `impact_score > 60`. `null` means the filter failed; the article should be processed again |
| `affected_supplier_ids` | list | Affected suppliers as `supplier_items.id` values. **Only filled for `direct` articles** |
| `event_type` | string | One of the seven types below |
| `filter_reason` | string | Short reason (for debugging) |

**Event types** (same values as `article_analyses.event_type` in the database):

| Code | Meaning |
|---|---|
| `tariff_increase` | A Turkish customs duty or other tax on the part (VAT, special consumption tax, Culture Fund) goes up, drafts included |
| `tariff_decrease` | Such a duty or tax goes down or is removed (e.g. a trade agreement) |
| `trade_restriction` | Ban, quota, licence, sanction or new mandatory certificate: the part cannot leave the origin country or enter Turkey without it |
| `transport_disruption` | Strike, disaster or closure at a departure or arrival port or airport (problems on the sea route between them, e.g. canals, do not count) |
| `price_change` | Concrete, sharp change in the market price of a part we buy, or a forecast of one with a figure (status `unclear`) |
| `other` | Affects a supplier but fits none of the above (e.g. the part is discontinued) |
| `not_relevant` | `none` articles |

### Impact analysis (Nemotron 3 Ultra)

`analysis` is only filled for `direct` articles; it is `null` for `none` articles and on errors.

| Field | Type | Description |
|---|---|---|
| `status` | string | **`enacted`** = decided or in force. **`proposed`** = draft or plan. **`ongoing_event`** = disruption happening now. **`unclear`** = the article does not say |
| `affected_suppliers` | list | `supplier_id` and a short reason `why` for each supplier |
| `country` | string / null | Country the measure or event concerns |
| `affected_locations` | list | Transport disruptions only: the departure or arrival points hit, as written in the supplier list (e.g. `"Kaohsiung Limanı"`); names not in the list are removed. Empty for other event types |
| `rate_type` | string / null | Which tax the rates belong to: `gv` (customs duty), `igv` (additional customs duty), `kultur_fonu` (Culture Fund), `kdv` (VAT), `otv` (special consumption tax). Null if the article is not about a tax or does not say which one |
| `old_rate_pct`, `new_rate_pct` | number / null | Previous and new rate in percent (`30` = 30%). **Only if stated in the article** |
| `effective_date` | `YYYY-MM-DD` / null | Date the measure takes effect. Usually null for drafts and ongoing events |
| `expected_delay_days` | int / null | Expected shipment delay for transport disruptions. **Only if stated in the article**; weeks and hours are converted to days (2 weeks = 14, 72 hours = 3); for a range the largest number is used. Null for other event types |
| `price_change_pct` | number / null | Price changes only: change in the part's market price in percent, with a sign (`40` = up 40%, `-5` = down 5%). **Only if stated in the article**; for a range the largest number is used |
| `summary` | string | 2–3 sentence summary in English, written for a procurement manager |
| `evidence_quote` | string | Supporting quote **in the article's original language**, so it can be found in the source |

### Control fields

| Field | Description |
|---|---|
| `warnings` | Corrections the agent made, e.g. an unknown supplier id was removed; the filter and the analysis disagreed on suppliers or event type (the analysis is used); **the filter marked the article relevant but the analysis did not** (the article becomes `none` with score 10 and `analysis: null`; both reasons are in the warning) |
| `errors` | Failed steps. `impact_level: null` means the filter failed; `analysis: null` with errors means the analysis failed. These articles can be processed again |

## Impact score

The score is computed in code, so the same facts always give the same score.

1. **Certainty sets the band:** in force or ongoing 80–100, proposed 66–79, unclear 61–65,
   not relevant 10. Every relevant article is above 60.
2. **Size sets the place inside the band** (0–20 points, spread over the band):
   - suppliers: 2 points per affected supplier, at most 10
   - event, at most 10: tariff or tax increase ½ point per percentage point of increase
     (new − old rate; the new rate alone if the old one is not stated); transport disruption
     10 points for a delay of 14 days or more, proportionally less for shorter; trade restriction
     5 points; price increase ¼ point per percent
   - only what is bad for us counts: a duty cut, a price drop and a VAT change (deductible, so no
     cost change) stay at the bottom of their band; a value the article does not state adds nothing

Examples: Suez Canal diversions, 6 suppliers, 14 days → 100; port strike, 6 suppliers, 4 days → 93;
additional duty 11% → 20%, 1 supplier → 86; draft 15% duty, 1 supplier → 72; trade agreement
removing duties → 80.

## `run`: run information

| Field | Description |
|---|---|
| `started_at`, `finished_at` | Run time (UTC) |
| `mock` | `true` for a dry run: placeholder results, do not use |
| `counts` | `direct`, `none`, `error` and `total` article counts |
| `filter`, `analysis` | Model id, number of calls, failed calls, tokens and estimated cost (USD) |
| `estimated_cost_usd` | Estimated cost of the run at Token Factory prices |
| `input_warnings` | Records skipped while reading the news file (duplicates, empty articles) |

## Database mapping

| JSON field | Table.column |
|---|---|
| `article_id` (database mode) or the article with the same `source_url` | `article_analyses.article_id` |
| `scan_log_id` (database mode) | `article_analyses.scan_log_id` |
| `is_relevant` | `article_analyses.is_relevant` |
| `impact_score` | `article_analyses.impact_score` |
| `event_type` | `article_analyses.event_type` |
| `analysis.summary` | `article_analyses.summary` |
| `analysis.rate_type`, `old_rate_pct`, `new_rate_pct`, `expected_delay_days` | `article_analyses` columns of the same name |
| `analysis.price_change_pct` | `article_analyses.price_change_pct`, once that column is added to the database (skipped until then); also part of `impact_score` |
| `analysis.country` (relevant articles) | one `article_impacts` row with `country_id` (matched on `countries.name_en`). **Not written when the article names no country or only Turkey.** So a tariff article with a country row is specific to that origin country ("20% on Chinese-origin power supplies"); one without applies to every origin ("VAT on monitors cut to 10%") |
| each name in `analysis.affected_locations` | one `article_impacts` row with `location_id` (matched on `locations.name`) |
| each id in `affected_supplier_ids` (= `supplier_items.id`) | two `article_impacts` rows: one with the `item_id` and one with the `supplier_id` of that supplier item |

Each `article_impacts` row names exactly one country, location, supplier or item, as the
database requires; each country, location and supplier is stored once per article. If `analysis` is null
(not relevant), the analysis columns stay empty and no impact rows are written. `analysis.status` has no
column: read it from the `impact_score` band (80–100 in force or ongoing, 66–79 proposed, 61–65 unclear).

## Consumers

| Component | Fields used |
|---|---|
| Cost calculation | `affected_supplier_ids`, `event_type`, `analysis.status`, `rate_type`, `old_rate_pct`, `new_rate_pct`, `effective_date`, `expected_delay_days` |
| Risk score | the fields above + `impact_score` |
| Database | the mapping above; articles with `errors` are processed again |
| User interface | `title`, `analysis.summary`, `analysis.evidence_quote`, `source_url`, `warnings` + the cost results |
