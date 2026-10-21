# Himalayan Sentinel

An AI-assisted disaster-risk **decision-support system** for Nepal. It preserves the original Next.js/FastAPI dashboard and light teal theme while adding persistent lake monitoring, private citizen evidence, administrator moderation and government-reviewed alerts.

**Automated risk assessment is experimental. This application does not make scientifically validated disaster predictions or issue authorized real-world emergency warnings. Follow Nepal's official authorities.**

What works:

- Public Nepal map, source lake polygons, basin/country/lake search, lake profiles and transparent score contributions.
- Static ICIMOD baseline ranks kept separate from dynamic indicators, exposure, confidence and monitoring priority.
- Private image report with consent, demo guest verification, tracking, validation, duplicate detection and rate limits.
- Administrator moderation, provider health/retry/disable, user/jurisdiction management, thresholds/templates, audit and delivery logs.
- Government confirmation, field-verification requests, response checklist, export, editable alert drafts, approval, publication, expiry and resolution.
- Public alerts update every 15 seconds. AI drafts never publish automatically. Mock email/SMS logs send no messages.
- Optional Open-Meteo and Gemini adapters with explicit cached/stale/simulated/template modes. Core demo needs no external API key.
- Local PostgreSQL/PostGIS or Compose deployment with spatial indexes and versioned migrations; SQLite fallback for development.

## Prerequisites

Python 3.12+, Node.js 22+, Git; `uv` recommended. Docker Desktop/Engine is optional for PostGIS. PowerShell instructions below run from the repository root. Use your existing licensed files in `data/`; do not move or alter originals.

## Local setup

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cd backend
uv sync --locked
uv run python -m app.db
uv run python -m app.scripts.seed_demo
uv run python scripts/inspect_datasets.py
uv run python scripts/preprocess_datasets.py
uv run python scripts/import_geospatial_data.py
uv run python scripts/import_context_data.py
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**. Staff sign-in: **http://localhost:3000/operations**. API/OpenAPI: **http://localhost:8000/docs**. For Windows without `uv run`, use `backend/.venv/Scripts/python.exe` from the appropriate working directory. On Linux/macOS the interpreter is `.venv/bin/python`.

Staff navigation uses shareable section links such as `/operations#overview` and `/operations#users`. The sidebar remembers its desktop collapse setting and becomes a keyboard-accessible drawer on mobile. Development output uses `.next-dev`; production builds use `.next` so builds do not overwrite a running development server's files.

After dependencies are installed, `./scripts/dev.ps1` starts both applications, migrations and seeds, and imports the local PDGL inventory when available. It preserves existing `.env` and account credentials. Ctrl+C stops the processes it started.

The helper also prepares broader lake/historical context and starts the 30-minute weather worker. Restart the API after changing `.env`. Live weather is enabled in the example configuration; use `WEATHER_LIVE=false` for an explicitly simulated offline demonstration. To check a single current forecast from `backend`, run `uv run python -m app.scripts.sync_weather --district rasuwa`; success requires an actual live response. A failed network request never counts as verified live data.

The public **Explore district evidence** section and **/evidence?district=rasuwa** show the broader lake inventory, historical GLOF records, district weather and modelled population context. Staff monitoring contains the same explorer, and the alert composer links to the incident district's evidence. Historical records are not predictions; district membership is geographic context rather than a downstream impact footprint. The original eight regional cards remain explicitly simulated.

Licensed boundaries ship in `backend/assets/boundaries/` with attribution and source hashes. Other local source files are optional and stay under ignored `data/`; the public source catalog shows what is available. `scripts/import_context_data.py` reproducibly prepares the 2015 inventory and the latest local GLOF CSV revision; it never combines overlapping revisions. WorldPop is summed within district boundaries only after verifying the exact product metadata. All contextual counts are separate from the dangerous-lake monitoring score. See [integration status](docs/integration-status.md), [source catalog](docs/data-catalog.md) and the guided [scope](devpost/scope.md), [requirements](devpost/prd.md), [technical plan](devpost/spec.md) and [build record](devpost/checklist.md).

The API migrates on startup as well; the explicit migration command is useful for deployment checks. Both seeds and imports are idempotent. No database or original dataset is committed. Without licensed local lake files, the public lake section shows an honest empty state; the original eight-region simulation remains available.

To use an existing PostgreSQL installation, install its compatible PostGIS extension package first ([official Windows instructions](https://postgis.net/documentation/getting_started/install_windows/)). Create a dedicated `himalayan_sentinel` database through your normal PostgreSQL administration account, then set `DATABASE_URL` in the ignored root `.env` to `postgresql+psycopg://YOUR_USER:URL_ENCODED_PASSWORD@localhost:5432/himalayan_sentinel`. The migration enables PostGIS in that database; the database role needs permission to create the extension. Run the same migration, seed and import commands above. Keep passwords out of commands and Git; do not change the installation's authentication settings to bypass a missing credential.

Alternatively, put `DB_USERNAME` and `DB_PASSWORD` in the private root `.env` (optional `DB_HOST`/`DB_PORT`, default localhost:5432), then run `uv run python -m app.scripts.setup_local_postgres` from `backend`. The helper creates the dedicated database, enables PostGIS and saves a correctly encoded `DATABASE_URL` without printing credentials. Use `--from-commented` only when you explicitly intend to read credentials stored as commented settings. PostgreSQL credentials must have database/extension creation privileges for this setup step.

PostGIS stores the imported lake and administrative polygons as spatial geometry with GiST indexes. It enables containment, distance and area queries; assessment scores remain separate application logic.

## One-command Docker startup

Copy `.env.example` to `.env`, then:

```powershell
docker compose up --build
```

Compose starts PostgreSQL 16/PostGIS, API, scheduler and frontend. Root `data/` is mounted read-only; private evidence, processed output and PostgreSQL use persistent volumes. The development API seeds from environment and imports PDGLs if installed. Docker must be running. The supplied Compose file is a **local demonstration setup**, with demo verification enabled and mock notification delivery. Do not expose it as an operational warning service.

## Environment

Root `.env.example` is the authoritative local example; it is ignored after copying to `.env`. Backend also reads `backend/.env` if present (it takes precedence). Frontend may use `frontend/.env.local` with `NEXT_PUBLIC_API_URL` to change the API address; rebuild for production.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite default in development; Compose overrides with PostgreSQL+psycopg |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Explicit development seed credentials |
| `GOVERNMENT_EMAIL`, `GOVERNMENT_PASSWORD` | Explicit development official credentials |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Compose database settings; use URL-safe credentials or URL-encode database URLs |
| `CORS_ORIGINS` | Comma-separated exact browser origins |
| `ENVIRONMENT` | `development` for demo; production refuses insecure cookies/demo verification |
| `DEMO_VERIFICATION` | Labelled mock guest check; production submissions disabled until real verification exists |
| `COOKIE_SECURE` | Enable under HTTPS; false only for local HTTP |
| `WEATHER_LIVE` | false uses labelled fixture; true enables Open-Meteo |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional structured draft explanation; no key uses labelled deterministic template |
| `STORAGE_DIR` | Private evidence path, default `backend/var/evidence` when run from backend |
| `NEXT_PUBLIC_API_URL` | Browser API root; never put secrets in NEXT_PUBLIC variables |

Demo account values are supplied **only in `.env.example`**, then read from environment. With an unchanged example: admin `admin@himalayansentinel.local`, official `officer@himalayansentinel.local`; both use the example password shown there. Change those local demonstration credentials before any deployment. Seeding never overwrites an existing account's password or jurisdiction choices.

## Tests and checks

Current preparation results, publication audit and remaining entrant actions are recorded in [submission status](devpost/submission-status.md) and the [repository handoff](docs/repository-handoff.md). Video work is deferred; no submission or eligibility approval is implied by passing checks.

```powershell
cd backend
uv run pytest -q
uv run ruff check app scripts tests
uv run ruff format --check app scripts tests
cd ../frontend
npm run typecheck
npm run build
npm run test:e2e
```

Browser tests use system Google Chrome (Playwright `channel: chrome`), a fresh isolated temporary SQLite database and ports 8010/3100. They exercise citizen image submission → admin evidence review → government confirmation → draft/approval/publication → public visibility → resolution; error states, route protection and lake details. Change the Playwright browser channel or install its Chromium if Chrome is unavailable. No test calls live data/AI APIs. The optional local dataset test skips when licensed data is absent. Screenshots/traces remain ignored under frontend/test-results.

Docker Desktop must use **Linux containers** for the supplied images. Check with `docker info --format '{{.OSType}}'`; on Windows the available engine can be selected with `docker desktop engine use linux`. Check existing containers before changing engines.

Run the same backend workflow suite against PostgreSQL/PostGIS with `docker compose --profile test run --build --rm backend-tests`. Each test creates and removes a separate temporary schema; application tables and evidence are preserved. Run the production frontend build and browser tests sequentially because Next.js generates type declarations during both checks.

For an already configured native PostgreSQL database, run from `backend`:

```powershell
$env:TEST_POSTGRES = '1'
try { uv run pytest -q } finally { Remove-Item Env:TEST_POSTGRES }
```

## Background jobs and deterministic demo

```powershell
cd backend
uv run python -m app.jobs --once
uv run python -m app.jobs
```

Weather synchronization, assessment recalculation, stale checks, expired-alert handling and session/rate-limit cleanup run every 30 minutes. The synchronous mock notification adapter records delivery at publication. Imports/quality audits are explicit reproducible CLI jobs. See [demo-script](docs/demo-script.md) for the timed walkthrough and `demo_scenario --phase baseline` / `--phase rainfall` commands. Stop the scheduler during that controlled synthetic scenario.

## Data and scientific limits

Local audit: 47 PDGLs (21 Nepal, 25 China, 1 India), 3,624 broader inventory lakes, 77 districts, 7 provinces, 4 historical GLOF CSV revisions and a WorldPop population raster. Original bytes remain untouched. Only PDGL polygons/attributes are imported into monitoring; boundaries supply map context. Historical outcomes are audited, not used to train a classifier. Population raster auditing does not establish downstream exposure.

ICIMOD. (2020). Potentially dangerous glacial lakes in the Koshi, Gandaki, and Karnali river basins of Nepal, the Tibet Autonomous Region of China, and India [Data set]. ICIMOD. https://doi.org/10.26066/RDS.1971950

Source metadata permits lake-data use with attribution. WorldPop raster tags and GLOF metadata state CC BY 4.0; the runtime boundaries are now bundled from Open Knowledge Nepal under CC BY 4.0 with a pinned revision and hashes. Original unverified boundaries remain excluded and unused. OpenStreetMap attribution is displayed on maps; optional weather is attributed to Open-Meteo. Full provenance, schemas, agreements and integrity results: [data catalog](docs/data-catalog.md), [generated file audit](docs/data-audit.md).

The regional trends, river readings, population exposure and initial counts are labelled simulated. No calibrated flood footprint, actual snowmelt estimate, satellite lake change, verified emergency-resource directory, real notification delivery or production guest verification is configured. No ML model is forced onto outcome-only historical data. Missing data reduces evidence coverage; it never establishes safety.

## Deployment and documentation

Deploy the built frontend and FastAPI behind a same-site TLS reverse proxy. Configure exact origins and secure cookies, a managed PostGIS database and private persistent evidence storage. Run migrations with extension privileges; use a restricted runtime database role. Provision real officials deliberately, replace verification/notification adapters, configure backups and retention, and validate methods with local experts before operational use. For a remote frontend, set its public API URL before build. Never distribute development credentials as production accounts.

- [Architecture](docs/architecture.md)
- [Risk methodology](docs/risk-methodology.md)
- [Security and privacy](docs/security-and-privacy.md)
- [Hackathon compliance and outstanding verification](docs/hackathon-compliance.md)
- [Implementation checklist and verification record](docs/implementation-plan.md)
- [Three-minute demo](docs/demo-script.md)

Health checks: `/health`, `/health/database`, `/health/providers`. Core versioned APIs are discoverable in OpenAPI. Deprecated public report endpoints return 410 to protect privacy; the existing regional risk/explanation APIs remain compatible.

MIT applies to application code; third-party datasets retain their own licences. Devpost submission/video upload and confirmation of historical Skill Pack usage remain entrant responsibilities.
