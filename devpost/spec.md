---
doc: spec
status: approved
---

# Himalayan Sentinel — Technical Plan

## How This Works, In Plain Language

The importer prepares the local lake and historical-event files without changing the originals. The backend serves bounded searches and district context. Weather comes from a separate live provider with timestamps and caching. Population totals are calculated only within the selected district. The browser lets a responder inspect this evidence before using the existing human-reviewed notice workflow.

## Authorization

This is an agent-authored implementation plan under the learner's instruction to complete the project, based on the approved scope. The learner delegated detailed choices; no separate interview or hands-on review is claimed. Retain the established Next.js/FastAPI stack.

## The Core Journey Through the System

Implements `prd.md > The Core Journey`. Local files → reproducible processed context → FastAPI context endpoints → public/staff evidence explorer. District selection → stored weather forecast and district population context. Staff review evidence → existing incident/alert API → approved demo notice → public polling.

## Stack

Reuse Python 3.12, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://docs.sqlalchemy.org/en/20/), [Rasterio](https://rasterio.readthedocs.io/), [Shapely](https://shapely.readthedocs.io/), Next.js/React/TypeScript, React Leaflet and Recharts from the installed manifests. No new hosted platform is required.

## Components

### Local Context Data

Implements `prd.md > Evidence Explorer` and `prd.md > Population Context`. New `backend/app/context_data.py` prepares/loads local context. A new `backend/scripts/import_context_data.py` writes atomic processed files under ignored `backend/data/processed/`. Prefer source hashes/cache keys, deterministic IDs and modification-aware caches. Broader lakes stay separate from `db.lakes`, preserving original dangerous-lake assessments. Latest historical revision only; missing values and approximate dates retained. District filtering uses actual geometry containment/intersection. District population uses Rasterio window/mask, finite nonnegative values and NoData exclusion with exact product provenance. Persistent cached aggregates are reproducible and invalidated on source changes.

### Context API Contract

New router `backend/app/context_api.py`, prefix `/api/v1/public/context`:

- `GET /catalog` → `{sources: [{id, name, status, count, source_date, attribution, limitations}], districts: [{id, name}], limitations: string}`.
- `GET /lakes?q=&country=&basin=&district=&offset=0&limit=50` → `{items: [{id, name, country, basin, district?, lat: number|null, lng: number|null, geometry: GeoJSON|null, properties: object, attribution, source_date}], total, offset, limit}`.
- `GET /events` with the same filters → `{items: [{id, name, country, basin, district?, lat: number|null, lng: number|null, geometry: GeoJSON|null, year: string|null, date: string|null, date_precision, impact: string|null, properties: object, attribution, source_date}], total, offset, limit}`.
- `GET /population/{district}` → `{status, district, population: number|null, year: 2026, units: "people", attribution, source, method, valid_cells, limitations}`; unavailable sources give a structured status, invalid district gives 404. Source-specific extra provenance fields are allowed.

All filter lengths and page sizes are bounded. Return JSON-safe values and useful missing-file states. Never expose raw paths, private reports or credentials.

### Weather

Implements `prd.md > Current Weather`. Keep `WeatherProvider` and existing observations table. Correct cache behavior for disabled/live modes and forecast expiry; synchronize source health and timestamps. Add a public district forecast route if needed for coverage beyond the eight original fixture regions. Reuse verified district geometry representative points as weather locations. Fetch only when requested or via an explicit bounded sync; scheduled lake refresh must avoid thousands of context requests. Tests use fake HTTP responses. Actual live verification is separate from tests.

### Evidence Interface

Implements `prd.md > Evidence Explorer` and `prd.md > Evidence to Notice`. New `frontend/components/evidence-explorer.tsx` and `context-map.tsx`, plus shared context types. Render on public dashboard and staff monitoring. District selector, source cards, tabs, filters, bounded list/map, weather and population panels. Cancel/ignore obsolete fetches to prevent stale selection results. Display values as React text, validate source links before rendering external URLs, and preserve accessible/mobile behavior.

## Data Model

Original local datasets remain read-only. Processed JSON and population caches remain ignored. Successful forecasts persist in the existing observations table with actual source and retrieval timestamps; stale/simulated mode must not change merely because a record was cached. Existing report/incident/alert tables retain their authorization and lifecycle semantics. No schema expansion is needed for contextual static records.

## File Structure

```text
backend/app/context_data.py       # context preparation, filters and population
backend/app/context_api.py        # public read-only context routes
backend/scripts/import_context_data.py
backend/app/providers.py          # live/cached weather provenance
backend/app/workflow.py           # existing workflows and district forecast
backend/tests/test_context_data.py
frontend/components/evidence-explorer.tsx
frontend/components/context-map.tsx
frontend/lib/context-types.ts
frontend/tests/evidence.spec.ts
scripts/dev.ps1                  # native local startup/import/worker
devpost/                        # scope, requirements, plan, checklist and map
docs/                           # technical evidence and demonstration guidance
```

## External Services and Dependencies

[Open-Meteo](https://open-meteo.com/en/docs): GET `https://api.open-meteo.com/v1/forecast`, latitude/longitude, daily precipitation_sum and temperature_2m_max, seven days, Asia/Kathmandu; response validated against equal-length daily arrays. Public noncommercial endpoint needs no AI key; respect [usage terms](https://open-meteo.com/en/pricing), cache and throttling. Existing Gemini is optional draft prose only. No Earth Engine/DHM access is claimed without a configured and tested route. [WorldPop release](https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf) and local raster tags must support product interpretation.

## Important Failure Modes

Missing local source → source unavailable and no invented records. Network failure → explicit stale cache or simulated fixture. Invalid geometry/date/NoData → preserve missingness or reject with actionable import diagnostics. Missing district overlap → no record membership inferred. Source licences remain documented separately from code's MIT licence.

## Where It Runs and How Someone Tries It

Native Windows: `./scripts/dev.ps1` after installing dependencies. Backend alone from `backend`: `.venv/Scripts/python.exe -m uvicorn app.main:app --reload`. Frontend: `npm run dev`. Public http://localhost:3000, staff /operations, API /docs at port 8000. Import contextual files with `.venv/Scripts/python.exe scripts/import_context_data.py` from backend. Private root `.env` controls live weather; real credentials never enter public files. Video and public repository publication require separate authorized actions.

## Look and Feel

Implements `prd.md > Look and Feel`. Extend the existing light teal cards and responsive grids, with clear section headings, source badges, bounded map height and textual record details. Keep controls operable with keyboard and readable at 390 px width.

## Decisions and Open Issues

The learner asked whether AI keys unlock live data. The agreed investigation separates data-source access from model access: verify actual Open-Meteo success and cache behavior without a Gemini key. All implementation choices derive from the delegated scope; no independent scientific calibration or external-service access is inferred. Hands-on user feedback and final submission artifacts remain truthfully recorded as pending until performed.

## Submission preparation revision - 19 October 2026

Runtime administrative boundaries use `backend/app/boundaries.py` and the pinned, licensed assets in `backend/assets/boundaries/`. Public GeoJSON routes and spatial imports use the same bundle as context filtering and population summaries. Synthetic tests explicitly inject custom boundary directories. The source manifest records upstream hashes; original raw boundaries are excluded and unused. Boundary changes invalidate population caches. Evidence and map panels display source attribution.

Repository: https://github.com/dhirajs16/himalayan_sentinel. Public access remains to be verified without authentication. Video recording/editing/upload are explicitly deferred as of 21 October; see `../docs/demo-checklist.md`. A public video URL is still required. `submission-status.md` tracks remaining shipping work and `submission-workbook.md` holds prompts for entrant-written answers. Public organizer guidance on Skill Pack timing was found on 21 October; see `../docs/organizer-clarification.md` before claiming eligibility.
