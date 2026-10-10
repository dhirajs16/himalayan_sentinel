# Himalayan Sentinel

> An AI-assisted flood and GLOF risk dashboard for Nepal that turns weather, hydrology, climate, and community signals into explainable local warnings.

Himalayan Sentinel is a hackathon proof of concept for **Devpost Build with AI: Basics**. It combines weather signals, seeded hydrology indicators, glacial-risk context, population exposure, and community observations into transparent local risk levels. It helps citizens, municipalities, and responders understand *why* an area may be at risk and prepare simple alerts in English or Nepali.

**This is a decision-support and risk-awareness prototype, not an official disaster warning or scientifically validated GLOF prediction system.** Always follow Nepal's government and local disaster authorities.

## What works

- Interactive OpenStreetMap view of eight Himalayan districts/corridors
- Deterministic, inspectable five-factor risk scoring
- Selected-region details and seven-day seeded trends
- Plain-language English and Nepali risk explanations
- SMS-style advisory and preparedness checklist generation
- Community observation submission
- Open-Meteo forecast proxy endpoint
- Full offline/demo fallback data in the frontend

## Tech stack

- Frontend: Next.js, TypeScript, Tailwind CSS, React Leaflet, Recharts
- Backend: FastAPI, Pydantic, httpx
- Planned production services: Supabase PostgreSQL, Vercel, Render, OpenAI or Gemini
- Map tiles: OpenStreetMap contributors

## Project structure

```text
frontend/       Next.js dashboard
backend/app/    FastAPI routes, schemas, scoring, seeded data
backend/tests/  API smoke tests
scope.md        Hackathon scope
prd.md          Product requirements
spec.md         Technical specification
```

## Run locally

Prerequisites: Node.js 20+ and Python 3.12+ (or `uv`).

### Backend

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

The API runs at `http://localhost:8000`; Swagger docs are at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment variables

Frontend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Backend (optional for the current MVP):

```env
CORS_ORIGINS=http://localhost:3000
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
```

No secret is required for the complete demo flow. AI endpoints currently use safe deterministic templates and are ready for a provider adapter.

## Risk scoring

The backend—not the language model—calculates every score:

```text
rainfall 30% + river level 25% + glacial context 20%
+ community reports 15% + population exposure 10%
```

Scores map to Low (0–25), Moderate (26–50), High (51–75), and Critical (76–100).

## APIs and data

- [Open-Meteo](https://open-meteo.com/) for optional live precipitation forecasts; no key required under its published terms
- [OpenStreetMap](https://www.openstreetmap.org/) map tiles and attribution
- Seeded/mock data for hydrology, glacial-risk context, population exposure, trend lines, and initial community report counts
- In-memory community reports in the current prototype; Supabase is the planned durable store

## Three-minute demo script

1. Introduce the problem and point out the prototype disclaimer (20s).
2. Scan summary cards and explain map colors (25s).
3. Select Rasuwa, show the score and its five transparent inputs (35s).
4. Compare its seven-day rainfall/risk trend (20s).
5. Switch to Nepali and generate a citizen advisory (30s).
6. Submit a community observation (25s).
7. Show the FastAPI docs or scoring formula and close with future impact (25s).

## Deploy

- Frontend: import `frontend/` into Vercel and set `NEXT_PUBLIC_API_URL`.
- Backend: deploy `backend/` to Render with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Set `CORS_ORIGINS` to the final Vercel origin.

## Limitations

- Hydrology, glacial-risk, population, trend, and initial report data are mock/seeded.
- Community observations are not verified incidents and reset when the API restarts.
- The current AI copy uses deterministic templates rather than a hosted model.
- This is not an official warning system and does not replace disaster agencies.
- Scientific GLOF prediction requires satellite imagery, field sensors, hydrological modelling, and expert validation.

## Future improvements

Add Supabase persistence and moderation, official DHM feeds where licensed, provider-backed summarization with guardrails, geospatial district boundaries, authenticated municipal workspaces, accessible low-bandwidth/PWA delivery, and expert validation.

## License

MIT — see [LICENSE](LICENSE).
