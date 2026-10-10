# Technical Specification

## Architecture
`Next.js client → FastAPI API → Open-Meteo / optional Supabase and AI provider`

The current proof of concept stores submitted reports in process memory. Seeded region, hydrology, glacial context, exposure, and trends are explicitly mock demonstration data.

## Risk model
`rainfall × .30 + river level × .25 + glacial context × .20 + community reports × .15 + population exposure × .10`

Thresholds: Low 0–25, Moderate 26–50, High 51–75, Critical 76–100.

## API
- `GET /health`
- `GET /regions`, `GET /regions/{id}`
- `GET /risk/latest`, `POST /risk/calculate`
- `GET /weather/{region_id}`
- `GET /reports`, `POST /reports`
- `POST /ai/explain-risk`, `POST /ai/generate-alert`

## Resilience
The frontend includes the same seeded dataset as a network fallback. Explanation and alert endpoints use deterministic templates, so the core flow does not depend on paid AI access. A production extension can add provider calls without moving scoring out of `risk_engine.py`.

## Data ethics
Community reports are unverified observations. The UI must not label them as confirmed incidents. Every generated explanation and alert includes an official-warning disclaimer.
