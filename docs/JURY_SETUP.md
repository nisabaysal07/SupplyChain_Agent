# Jury setup and evaluation guide

This guide walks you through installing ChainGuard (SupplyChain Agent) from scratch on your own computer.
Setup takes about **15–20 minutes**. Commands are for Windows PowerShell; macOS/Linux differences are noted.

There are two ways to try it:

| Path | Requirements | What you see |
|---|---|---|
| **A. Without API keys** | Docker, Python, Node.js | Alerts and cost impacts built from the news already in the seed database, the map, and the full panel |
| **B. Live scan** | A + Tavily and Nebius API keys | In addition, a real-time news scan and LLM agent analysis |

## Login

The admin account below is created automatically the first time the panel starts (the values are already in `.env.example`):

| Field | Value |
|---|---|
| URL | http://localhost:3000 |
| E-mail | `yonetici@chainguard.test` |
| Password | `RCSP0v2Iwsk1H112R_e0` |

> This account is for local evaluation only. It is created only when the panel starts with **no users yet**;
> changing the values in `.env` later does not change an existing account (see [Troubleshooting](#troubleshooting)).

## 1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — must be running
- [Python 3.11+](https://www.python.org/downloads/) — tick "Add Python to PATH" during installation
- [Node.js 22+](https://nodejs.org/)
- [Git](https://git-scm.com/)

Check:

```powershell
docker --version; python --version; node --version
```

## 2. Get the project

```powershell
git clone https://github.com/nisabaysal07/SupplyChain_Agent.git
```

```powershell
cd SupplyChain_Agent
```

## 3. Create the configuration files

Two `.env` files are needed. You can use the values below as they are.

**a) `.env` in the project root** (`SupplyChain_Agent/.env`) — copy `.env.example`:

```powershell
Copy-Item .env.example .env
```

Then open `.env` in a text editor and replace its contents with:

```ini
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=supply_db
POSTGRES_USER=proje_admin
POSTGRES_PASSWORD=JuryDemo2026!

# Panel login (first admin)
NUXT_ILK_YONETICI_EPOSTA=yonetici@chainguard.test
NUXT_ILK_YONETICI_SIFRE=RCSP0v2Iwsk1H112R_e0

# Session cookie key and model API token (at least 32 characters each)
NUXT_SESSION_PASSWORD=jury-demo-session-key-0123456789abcdef
NUXT_MODEL_API_TOKEN=jury-demo-model-token-0123456789abcdef

PANEL_URL=http://localhost:3000

# Path B (live scan) only; leave empty for path A
TAVILY_API_KEY=
NEBIUS_API_KEY=

# Notification channels (optional); empty = notifications are only printed to the console
NOTIFY_URLS=
```

**b) `kurulum/.env`** — for Docker. The Postgres password must be the **same** as in the root `.env`:

```powershell
Copy-Item kurulum\.env.example kurulum\.env
```

Contents of `kurulum/.env`:

```ini
POSTGRES_USER=proje_admin
POSTGRES_PASSWORD=JuryDemo2026!
POSTGRES_DB=supply_db
QDRANT_API_KEY=jury-demo-qdrant-key
```

## 4. Start the database

From the project root:

```powershell
docker compose -f kurulum/docker-compose.yml up -d
```

On first start the schema and seed data (the fictional company KurguTek's suppliers, parts, contracts, stock and
sample news) are loaded automatically. Wait ~20 seconds until `proje_postgres` shows `(healthy)` in `docker ps`.

Check (should print `11`):

```powershell
docker exec proje_postgres psql -U proje_admin -d supply_db -c "SELECT count(*) FROM locations"
```

> If another PostgreSQL already uses port 5432 on your machine: change `"5432:5432"` to `"5433:5432"` in
> `kurulum/docker-compose.yml` and set `POSTGRES_PORT=5433` in the root `.env`.

## 5. Set up Python

```powershell
python -m venv .venv
```

```powershell
.venv\Scripts\activate
```

macOS/Linux: `source .venv/bin/activate`

```powershell
pip install -r requirements.txt -r agent_core/requirements.txt
```

> If PowerShell says "running scripts is disabled", run this once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 6. Start the panel

Open a **new terminal** and, from the project root:

```powershell
cd tedarikci_paneli\web
```

```powershell
npm ci
```

```powershell
npm run dev
```

When you see `Listening on http://localhost:3000`, open http://localhost:3000 in your browser and sign in with the
[login details](#login). Keep this terminal open.

## 7. Fill the panel with data

### A. Without API keys

In the first terminal (virtual environment active, project root):

```powershell
python risk_alerts.py --replay
```

```powershell
python panel_sync.py --all
```

The first command calculates cost impacts and alerts from the analyses already in the database; the second sends
them to the panel. Refresh the panel: the alerts appear on the **Events** page and in the notification bell.

To send only the sample events to the panel (second terminal, in `tedarikci_paneli\web`, server running):

```powershell
npm run ornek:gonder
```

### B. Live scan (with API keys)

Fill in `TAVILY_API_KEY` ([tavily.com](https://tavily.com)) and `NEBIUS_API_KEY`
([Nebius Token Factory](https://tokenfactory.nebius.com)) in the root `.env`, then:

```powershell
python main.py
```

The full chain — scan → agent analysis → cost impacts and alerts → panel → notifications — runs in a few minutes.
With only a Tavily key, `python main.py --no-agent` runs the scan alone.

## What to try in the panel

- **Dashboard** — risk summary, extra cost, parts that need reordering, and a map of the supply routes
- **Events** — events affecting suppliers, with severity, cost impact and source articles
- **Suppliers** — risk and stock status per supplier and part
- **Data Upload** — import company data from an `.xlsx` file (only adds new records)
- **Settings** — profile, notification preferences and news scan interval
- Language switch (English/Turkish) and the notification bell in the top bar

## Tests (optional)

In `tedarikci_paneli\web`:

```powershell
npm test
```

```powershell
npm run typecheck
```

To check the agent pipeline without API calls, in the `agent_core` folder:

```powershell
python -m agent --news data/examples/pc_test_news.json --dry-run
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Incorrect email or password" at login | The account may not have been created if `.env` was incomplete when the panel first started. Stop the panel (Ctrl+C), delete the `tedarikci_paneli\web\.data` folder, check `.env`, and start it again with `npm run dev`. |
| Panel terminal reports that `NUXT_ILK_YONETICI_SIFRE` is invalid | The password must be at least 12 characters; write it without quotes or spaces. |
| `password authentication failed` | `POSTGRES_PASSWORD` differs between the two `.env` files. Fix it and reset the database (below). |
| Missing tables / empty data | Reset the database: `docker compose -f kurulum/docker-compose.yml down -v`, then `docker compose -f kurulum/docker-compose.yml up -d` |
| `panel_sync.py` returns 401 | `NUXT_MODEL_API_TOKEN` in the root `.env` must be at least 32 characters; restart the panel after changing it. |
| Commands joined with `&&` fail | Windows PowerShell 5.1 does not support `&&`; run the commands one by one. |

Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)

## Uninstall

```powershell
docker compose -f kurulum/docker-compose.yml down -v
```

Then delete the `SupplyChain_Agent` folder.
