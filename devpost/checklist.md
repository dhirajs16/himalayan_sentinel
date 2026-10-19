---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast, selected under the learner's explicit request to complete the project autonomously. The displayed scope is approved by that request. Requirements, technical details and build order are delegated implementation decisions. Agent checks may proceed; learner hands-on checks must not be marked performed without feedback.

## Slices

- [x] **1. Explore real local evidence and population context**
  Becomes usable: Public/staff evidence explorer with searchable lake/event context and district population.
  Why now: Connect unused local files through to the screen and prove source provenance early.
  PRD ref: `prd.md > Evidence Explorer`, `prd.md > Population Context`
  Spec ref: `spec.md > Local Context Data`, `spec.md > Context API Contract`, `spec.md > Evidence Interface`
  Build: Prepare local files; implement endpoints, context interface and tests; preserve original inputs.
  Verify (mechanical): Import counts/hash preservation; backend context tests; TypeScript and browser evidence tests.
  Learner check: Open dashboard, search lakes/events and select Rasuwa/Gorkha; inspect source dates and population limits.
  Commit: `Integrate local geographic evidence and population context`

- [x] **2. Inspect live forecasts before reviewing a notice**
  Becomes usable: District forecasts with source timestamps, persistent caching and clear failure modes next to the reviewed notice workflow.
  Why now: Build on the evidence explorer and prove actual current data reaches the app.
  PRD ref: `prd.md > Current Weather`, `prd.md > Evidence to Notice`
  Spec ref: `spec.md > Weather`, `spec.md > Data Model`
  Build: Verify provider, cache/expiry/source health, district forecast routes, native/Compose refresh and evidence links in staff workflow.
  Verify (mechanical): Provider tests; actual live request; stored observations; full publication browser flow.
  Learner check: Select a district, inspect forecast source/mode/time, then review a staged report and demo notice.
  Commit: `Connect current forecasts to the evidence review journey`

- [ ] **3. Reproduce and demonstrate the finished integration**
  Becomes usable: Documented startup, verified demo flow, factual source catalog and navigable app map.
  Why now: Technical completion must be reproducible and limitations must match the actual implementation.
  PRD ref: `prd.md > Verification and Open Questions`
  Spec ref: `spec.md > Where It Runs and How Someone Tries It`, `spec.md > Decisions and Open Issues`
  Build: Update setup, source documentation, demonstration checks and app map; run existing checks and repair failures.
  Verify (mechanical): Backend tests/lint; TypeScript; production build; browser workflows; privacy/staging review.
  Learner check: Try the app and record any confusing or broken behavior before making the public submission.
  Commit: `Document and verify the integrated demonstration`

## Hands-on Checkpoints

- [ ] Evidence explorer tried by learner; feedback received.
- [ ] Final core journey tried by learner; feedback received.

## Final Review

- [ ] Learner confirms readiness after hands-on review.

## Code Tour and App Map

- [ ] Learning activity discussed with learner; no mastery inferred from explanation.
- [ ] Optional edit/reflection offered or declined.
- [x] `devpost/app-map.html` generated and checked against finished code.

Activity and evidence: implementation checkpoint `acd354d`; 44 backend tests pass against isolated SQLite and PostgreSQL/PostGIS, 9 browser tests pass, Python typing and lint/format checks pass. The production Next.js build passes with all five application/not-found routes. The actual running API and a separate real-browser check display prepared context, verified district population and current forecasts with zero browser runtime errors. The offline map was opened in Chrome and visually checked. It is a reference, not a completed learner activity.
Route and stops: importer → context API → evidence explorer; weather provider → stored observation → forecast panel.
Edit outcome: not performed by learner.
Reflection: not yet offered.
Activity mode: reference guide prepared during autonomous work; hands-on activity pending.

## Revisions

- Local evidence and weather were verified together as one integrated working checkpoint (`acd354d`), including the pre-existing supporting workflows needed to reproduce the application. No unrelated editor configuration or private data was included.
- Agent-authored requirements, technical details and build order proceed under the learner's explicit instruction to complete the project; unseen plans and hands-on activities are not described as personally reviewed or performed.
- Independent review identified case-sensitive district-link selection, Nepal-midnight rainfall indexing and duplicate concurrent weather fetches; all were repaired and covered by checks.
- A Windows PROJ database conflict was avoided by validating the raster WKT through PyProj and using the already verified WGS84 geometry directly; no machine configuration was changed.
- Browser tests completed successfully; their isolated Windows test servers required scoped cleanup before Playwright teardown returned exit code zero. The learner's development servers were preserved.

## Verification record

- Broader inventory: 3,624 records; latest historical revision: 766 events; district boundaries: 77; dangerous-lake inventory remains separate at 47.
- WorldPop district sums: Rasuwa 46,485.04 modelled people across 19,722 valid cells; Gorkha 249,877.77 across 96,812 valid cells. These are geographic context, not exposure estimates.
- Original source integrity: 33 file hashes checked against the existing audit; zero changes.
- Actual lake weather refresh: 47 locations, modes `[live]`, status `ok`; forecasts persist in the configured PostgreSQL database.
- Browser suite: 9 passed, including the existing publication/resolution journey and new filtering, pagination, source labels, district links, obsolete-response handling and mobile context.
- Privacy/staging: private `.env`, learner profile, raw datasets, evidence/database storage, generated derivatives and unrelated editor settings excluded from the implementation commit.
- Production build: successful Next.js compilation, type validation, static generation and build traces; `/evidence` is a dynamic route accepting a selected district.
- Actual application browser check: `/evidence?district=Rasuwa` on the learner's existing development server displayed the real catalog, modelled population and live/cached current forecast; zero page errors. Screenshot retained locally under ignored `frontend/test-results/live-evidence.png`.
- App map: browser opened the standalone local HTML, screenshot visually reviewed, no external assets required. `frontend/test-results/app-map.png` is an ignored local artifact.
- Startup helper: PowerShell parser reports no syntax errors. Existing API/frontend processes were preserved; the running API reloads the new code.

## Remaining learner and shipping work

The implementation and verification tasks are complete. The unchecked hands-on/learning boxes above require actual learner participation; automatic checks do not replace them. The learner can open `/evidence?district=rasuwa`, try the searches and reviewed-notice journey, and report any confusing or broken behavior. A short reference route is available in `app-map.html`; a harmless label edit or reflection is optional.

Public repository visibility/current remote content remain unverified. The configured origin exists locally, but an unauthenticated browser fetch was inconclusive. No push, visibility change, video upload, public deployment or Devpost submission was performed. Actual video URL, learner-authored form fields and submission confirmation remain entrant actions. `docs/demo-checklist.md` records the technical demonstration sequence and required artifacts.

