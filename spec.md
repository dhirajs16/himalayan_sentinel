# Technical specification

Next.js App Router + React/TypeScript + existing Tailwind theme, React Leaflet and Recharts connect to FastAPI/Pydantic through /api/v1. SQLAlchemy stores users, hashed sessions, private report metadata, incidents, alerts/versions/deliveries, sources/sync runs, observations, lake geometry and versioned assessment documents. SQLite supports local development; PostgreSQL migrations add PostGIS geometry and spatial indexes.

Raw files stay under data/. Reproducible Python scripts inspect, preprocess and import the local lake inventory. Static source rank, dynamic environment, exposure, completeness, evidence confidence and monitoring priority are separate concepts. The lake rules version persists every contribution and threshold. Legacy regional fixtures stay labelled simulated.

Opaque 15-minute access tokens remain in browser memory; eight-hour refresh tokens rotate through HttpOnly cookies. Server roles and assigned jurisdictions gate staff actions. Images have size/MIME/decoder/pixel checks, random private paths and metadata-free display derivatives. Public APIs never list unverified reports or exact reporter coordinates.

Reports: Submitted → admin Escalated/Rejected → official Field verification requested/Verified/Rejected → Confirmed incident. Alerts: Draft → Pending approval → Approved → Published/Updated → Expired/Cancelled/Resolved. A published revision remains visible while its replacement is reviewed; editing resets approval. Admins cannot authorize publication. Every consequential decision is audited.

Open-Meteo has timeouts, retry, persistent cache and explicit stale/demo handling. Optional Gemini returns schema-validated draft prose and supported evidence IDs; deterministic templates remain the offline fallback. AI cannot set scores or publish. Unsupported providers are explicit interfaces, not fabricated live feeds. A simple 30-minute scheduler recalculates and checks freshness/expiry.

See docs/architecture.md, docs/risk-methodology.md and OpenAPI at /docs for detailed contracts and limits. No production early-warning validation is claimed.

The guided integration technical plan is in [devpost/spec.md](devpost/spec.md). Contextual data is served separately through `/api/v1/public/context`; original dangerous-lake assessments and publication authorization remain separate. Source transformations and population aggregates are reproducible ignored derivatives. Live district forecasts use persistent observations and explicit source modes.
