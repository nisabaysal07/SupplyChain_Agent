# Supply Chain Risk Agent

An AI agent that reads news in any language and tells a Turkish manufacturer which of its
foreign suppliers are affected: new customs duties and taxes, trade restrictions, strikes or
disasters at the ports and airports on its routes, and sharp price changes of the parts it buys.

The agent runs on **NVIDIA Nemotron** models served by **Nebius Token Factory**.

## How it works

```
news articles ──► 1. Filter (Nemotron 3 Super) ──► relevant? ──► 2. Analysis (Nemotron 3 Ultra) ──► 3. Score ──► JSON
                     every article, one by one          │            relevant articles only            (code)
                                                        └─ no ──────────────────────────────────────────► score 10
```

1. **Filter.** Nemotron 3 Super screens every article against the supplier list and marks it
   relevant (`direct`) or not (`none`), with the event type and the affected suppliers.
2. **Analysis.** Nemotron 3 Ultra reads only the relevant articles. It receives the filter's
   suppliers as candidates, checks each one, and extracts the facts the cost calculation needs:
   tax type and old/new rate, effective date, status (in force, proposed, ongoing event),
   the ports and airports hit, expected delay in days, price change in percent, an English summary and a supporting quote in the original language.
3. **Score.** A 0–100 impact score is computed in code, so the same facts always give the same
   score. The status sets the band (in force or ongoing 80–100, proposed 66–79, unclear 61–65,
   not relevant 10); the number of affected suppliers and the size of the event (tax increase,
   delay in days, price rise) set the place inside it. An article is relevant when its score is
   above 60.

Ultra is also a second check on the filter. If it finds an article irrelevant, the alert is
dropped; if its suppliers or event type differ from the filter's, its answer is used and the
disagreement is recorded as a warning. Supplier ids that are not in the supplier list are discarded.

### What counts as relevant

| Event type | Example |
|---|---|
| `tariff_increase` / `tariff_decrease` | Turkey raises the additional customs duty on Chinese-origin motherboards; VAT on monitors is cut; a free trade agreement removes duties |
| `trade_restriction` | China requires export licences for graphics cards; Turkey requires an import licence for SSDs or a TSE certificate for monitors |
| `transport_disruption` | Strike at the Port of Mersin; typhoon closes a departure port or airport |
| `price_change` | DDR5 module prices rise 40%; analysts expect a 15% rise (recorded as unclear, lowest score) |
| `other` | A supplier stops making the part we buy |

Not relevant: factory incidents, measures between other countries, general freight trends,
problems at ports or airports the suppliers do not use, company news and opinion pieces.
A problem at a city's airport does not affect a supplier that ships from the same city's seaport.

## Model choice

| Stage | Model | Why |
|---|---|---|
| Filter (every article) | Nemotron 3 Super | Caught every alert in the test set at about a third of Ultra's price per token. Nemotron Nano missed alerts; Lightning did not return valid JSON. |
| Analysis (relevant articles only) | Nemotron 3 Ultra | More accurate supplier matching than Super; extracts rates, dates and delays correctly from articles in eight languages. |

The cheap model screens everything and the larger model only sees the few articles that matter,
so a run costs a few cents. Settings are in `agent/config.yaml` (temperature 1.0, reasoning
enabled in low-effort mode).

Design choices that came from testing:
- **One article per filter call.** In batches of six, Super once left an article out of its answer.
- **Candidate check.** Giving Ultra the filter's suppliers to verify fixed both missed and extra suppliers.
- **Shared definitions.** Both models see the same event-type definitions, so they classify events the same way.
- **English output.** Summaries are written in English regardless of the article's language;
  qualifiers such as "at least" and "up to" are kept as the article states them.

## Results

| Test | Result | Cost |
|---|---|---|
| 27 synthetic articles in 8 languages (16 relevant, 11 traps) | 27/27 correct: relevance, suppliers, event type, status, tax type and rates, dates, delay | ~$0.14 |
| 3 real articles (Typhoon Champi, Taiwan Taoyuan Airport) | 3/3 correct: only the supplier shipping from that airport | ~$0.02 |
| 10 real articles with no link to the suppliers | 10/10 correctly marked not relevant | ~$0.003 |

The test set with its answer key is in `data/examples/pc_test_news.json`.

## Project structure

| Path | Contents |
|---|---|
| `agent/` | The agent: pipeline, prompts, output schemas, scoring, Token Factory client, database storage (`save.py`) |
| `agent/OUTPUT_FORMAT.md` | Output fields and how they map to the database |
| `data/build_suppliers.py` | Builds `data/suppliers.json` from the project database (suppliers, parts, contracts, shipments, locations) |
| `data/suppliers.json` | The supplier list the agent works with; ids match `supplier_items.id` in the database |
| `data/examples/` | Synthetic test articles with the answer key |

The example company is fictional: a desktop PC manufacturer in Ankara with nine suppliers in
China, Taiwan, Vietnam and South Korea.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
```

Add your Nebius Token Factory API key to `.env`: `NEBIUS_API_KEY=...`

## Usage

```bash
# Rebuild the supplier list from the database (when supplier data changes;
# needs POSTGRES_USER, POSTGRES_PASSWORD and POSTGRES_DB in .env)
python data/build_suppliers.py

# Check the pipeline without API calls
python -m agent --news data/examples/pc_test_news.json --dry-run

# Run with Nemotron on Token Factory: the test set, or the new articles in the database
python -m agent --news data/examples/pc_test_news.json
python -m agent --db

# Analyse the new articles and store the results in the database (scheduled runs)
python -m agent --db --save

# Or store a results file after checking it
python -m agent.save output/agent_results_<timestamp>.json
```

Results are always written to `output/agent_results_<timestamp>.json`. In database mode the
agent reads the articles that have no analysis yet and stores its results in
`article_analyses` and `article_impacts`. Articles that already have an analysis are skipped,
and articles with errors are not stored, so the next run analyses them again. Input formats
are described at the top of `agent/news_loader.py`.
