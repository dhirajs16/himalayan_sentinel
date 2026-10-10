# Himalayan Sentinel — Scope

## Goal
Build a working decision-support prototype that helps people in Nepal understand local flood and GLOF-related risk signals and prepare clear, bilingual alerts.

## In scope
- Interactive Nepal risk map for eight seeded mountain districts
- Transparent five-factor risk score and four risk levels
- Region detail view, trends, exposure, and plain-language explanation
- English/Nepali citizen alerts and preparedness checklist
- Community observation form
- Live Open-Meteo endpoint with graceful seeded-data fallback
- Responsive dashboard and reproducible local setup

## Out of scope
- Scientific GLOF prediction, automated evacuation orders, sensor ingestion, official alert distribution, authentication, and production-grade incident verification

## Success criteria
The demo completes one end-to-end flow: select a region → inspect its factors → generate a bilingual alert → submit a community report. The score is always computed by deterministic backend logic, never by AI.
