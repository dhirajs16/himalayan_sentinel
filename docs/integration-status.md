# Integration status and reproduction

This file records the implemented scope and external dependencies. Guided development began on 19 October 2026 after the original application existed. It is technical documentation, not a claim of submission eligibility or operational deployment.

## Local evidence

The application serves the existing 47 assessed dangerous lakes separately from the broader 3,624-lake ICIMOD inventory. The broader inventory preserves static source attributes and does not acquire dangerous-lake ranks. The latest local historical GLOF revision contains 766 events; earlier overlapping revisions are not concatenated. Missing/approximate dates and unmapped records remain explicit. Source IDs and attribution are retained. District membership is computed geographically and does not represent a downstream hazard footprint.

Run from `backend`:

```powershell
.venv/Scripts/python.exe scripts/import_context_data.py
```

It writes derived `context.json` under ignored `backend/data/processed/` using atomic replacement. Raw files are unchanged. Public API:

- `/api/v1/public/context/catalog`
- `/api/v1/public/context/lakes?q=&country=&basin=&district=&offset=0&limit=50`
- `/api/v1/public/context/events` with the same filters
- `/api/v1/public/context/population/rasuwa`
- `/api/v1/public/context/weather/rasuwa`

The source catalog works when optional datasets are absent, with explicit unavailable states. Runtime administrative boundaries have been replaced with pinned Open Knowledge Nepal CC BY 4.0 data, bundled with attribution and hashes. The original unverified copies remain ignored and unused. Code licensing does not replace dataset licenses.

## Population

The exact local WorldPop file `npl_pop_2026_CN_100m_R2025A_v1.tif` is a constrained 2026 modelled population-count product. Its embedded metadata, CRS and resolution are checked before calculating values. The [WorldPop release statement](https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf) identifies estimated counts per grid cell. No density/area multiplier is applied.

The calculation sums finite nonnegative pixel values whose centres lie inside the selected district, excluding NoData. It uses bounded windows, records valid-cell coverage and caches results using source fingerprints and the district geometry. The alpha model estimate and boundary uncertainty remain visible. It is district population context, **not affected population, exposure or real-time occupancy**. A flood-exposure estimate would require a separate defensible impact footprint.

## Live weather

The existing [Open-Meteo forecast endpoint](https://open-meteo.com/en/docs) supplies precipitation and maximum air temperature with Nepal calendar dates. No Gemini key is required. The local `.env` now enables live weather; examples default to `WEATHER_LIVE=true`. A provider disabled in staff settings stays disabled even if a recent live cache exists.

Successful forecasts persist with retrieval time and forecast date. A recent cache covering today's Nepal date can be reused for 30 minutes; failed refreshes retain a clearly stale cache or return a labelled simulated fixture. Invalid arrays, negative rainfall, nonfinite values and unordered dates are rejected. A shared cooldown prevents a throttled request from triggering retries across all lake locations.

Run a single live verification from `backend`:

```powershell
.venv/Scripts/python.exe -m app.scripts.sync_weather --district rasuwa
```

The command exits successfully only after a genuine live fetch. A live Rasuwa seven-day response was retrieved and stored on 19 October 2026. Run it again to establish current connectivity; that one verification is not a guarantee of future service availability. Forecasts at representative locations are neither observed river gauges nor calibrated GLOF predictions.

`python -m app.jobs --once` refreshes assessed lake forecasts and assessments. `python -m app.jobs` repeats every 30 minutes. Native `scripts/dev.ps1` starts the worker; Compose already has a worker service. Stop/restart the local services after code/configuration changes.

## Evidence to notice

Public dashboard, dedicated `/evidence` and staff monitoring use the same bounded evidence explorer. The government alert composer opens contextual evidence for the incident's district in a separate tab. Staff decide which verified facts belong in the evidence summary; the software does not infer that a nearby lake caused a report. Existing report privacy, jurisdiction enforcement, approval, edited-version review and demo-only notification adapters remain in place.

## Follow-on integrations

| Source | Remaining dependency |
|---|---|
| Terrain | Appropriate elevation raster, acquisition route and method validation |
| Satellite water/change | Imagery dates, access, masking and comparable observations |
| GPM IMERG | Specific product/run, access route, units and accumulation processing |
| DHM hydrology | Verified authorized feed/exports, station metadata and thresholds |
| Infrastructure | Bounded inventory acquisition, coverage and spatial relevance |
| Operational warnings | Authorized operators, scientifically validated methods, reliable delivery and production identity |

These sources are explicit follow-on work under the approved scope. Their adapter placeholders do not count as successful integrations. Relevant acquisition research is in `devpost/integration-inventory.md`.

## Review and submission

Agent verification is recorded in `devpost/checklist.md`. Learner hands-on feedback must remain pending until actually supplied. A public repository, accessible video, human-authored submission fields and organizer decisions are separate from local technical completion. Publishing, visibility changes and external submission have not been authorized by a generic implementation request.

Verified final checks: 44 backend tests passed on SQLite and the same 44 on PostgreSQL/PostGIS; nine browser tests passed; Python typing across 20 modules, Ruff lint/format checks and frontend TypeScript passed; the production Next.js build passed. All 33 original dataset hashes matched the existing audit. An additional browser check against the actual running development app displayed the real source catalog, population and current forecast with no page errors. The offline app map was opened and visually checked. The full native helper/Compose lifecycle was not restarted during this iteration; existing development services were preserved.
