# Data integration inventory

Recorded 19 October 2026. Planning input for the Devpost Learn workflow.

## Requested direction

The learner asked to integrate the unused local datasets and disabled or unavailable data providers while following the installed Devpost skills. This records the requested direction and technical prerequisites; the scope, product requirements, and technical plan still need the guided conversations and review.

The application existed before the Skill Pack was installed. Today's work must be recorded as further development, with its actual timing. This inventory does not establish submission eligibility.

## Existing evidence

- Earlier checks in this session confirmed 47 potentially dangerous lakes in the configured PostgreSQL database and running public API, and 84 imported administrative boundaries. The public province endpoint returned seven features.
- The broader glacial-lake inventory, historical GLOF CSV revisions, and WorldPop raster are present under the read-only root `data/` directory.
- The existing documentation reports 3,624 broader inventory lakes and 766 events in the latest historical GLOF revision. These counts must be checked during import rather than assumed from documentation.
- Live weather was disabled when checked. Open-Meteo has an implemented forecast/cache/fallback adapter; the remaining named provider classes are unavailable interfaces.
- The original eight-region dashboard uses simulated indicators. Real inventory geometry and dynamic monitoring inputs have separate provenance.

## Integration candidates and prerequisites

| Source | Current implementation | Useful integration to define in planning | Prerequisites and limits |
|---|---|---|---|
| Open-Meteo | Forecast adapter exists; live mode disabled | Current forecast charts, cached observations, freshness, scheduled refresh and persistent provider status | Confirm endpoint use fits provider terms; bound requests, respect throttling, and verify an actual successful response. Keep forecasts separate from observed rainfall. Changing a flag alone is not completion. |
| Broader ICIMOD glacial-lake inventory | Local shapefile audited; not imported into public inventory | Searchable lake layer and profiles alongside the existing dangerous-lake inventory | Preserve source IDs, attribution and inventory identity; resolve overlapping source records without duplicating lakes or assigning dangerous-lake ranks to unranked records. Verify redistribution terms. |
| Historical GLOF database | Local CSV revisions audited | Historical-event map, filters and source-linked event details | Select the latest revision rather than concatenating revisions; retain approximate dates, missing coordinates and repeated events. Historical events do not establish a forecast model. |
| WorldPop | Local population raster audited | Population layer or summaries within explicitly selected areas | Verify this exact product's units, release, NoData and attribution. District or buffer population is geographic context; a downstream exposure calculation additionally needs a defensible hazard footprint. |
| Administrative boundaries | Local files served and imported | Geographic filtering and spatial joins where supported | Verify source/licence, boundary currency and coverage before claiming authoritative jurisdictions or republishing the files. |
| SRTM / terrain | Unavailable interface; no local elevation raster | Elevation and slope context for a defined study area | Acquire an appropriate DEM with documented source, resolution, vertical reference and NoData handling. Flow routing and inundation require additional methods and verification. |
| GPM IMERG rainfall | Unavailable interface; no local rainfall product | Recent precipitation estimates with product timestamps and accumulation windows | Choose the specific product/run, acquisition route and access requirements; process raster units, time windows and missing coverage. Satellite estimates and forecast rainfall must remain distinct. |
| Satellite water / Earth Engine | Unavailable interface; no authenticated integration | Dated water-extent layers or comparable lake-area observations | Select imagery, comparison dates, cloud/snow masks and quality checks. Earth Engine requires a registered Cloud project with the API enabled and suitable permissions; alternative acquisition routes can be evaluated. One static lake polygon cannot establish change. |
| DHM hydrology | Unavailable interface | Station observations and official thresholds where an authorized feed supports them | Verify a documented, permitted machine-readable feed or supplied exports, station metadata, observation units, timestamps and threshold meanings. A public website alone does not establish integration access. |
| OpenStreetMap infrastructure | Basemap tiles used; no infrastructure inventory | Dated roads, bridges or facilities as contextual layers | Choose a bounded data extract/query route, coverage, attribution and refresh policy. Infrastructure within a region is not automatically affected infrastructure. |

## Evidence needed to call an integration complete

For each selected integration, the technical plan should identify its source, access route, transformation and storage, public or staff interface, freshness and failure behavior, and a meaningful verification check. Demonstration data must retain its simulated label. Completion should be backed by real source records reaching the intended app screen.

## Suggested sequence for discussion

1. Finish `1-start` and capture the learner's background and learning intention.
2. Use `2-scope` to agree on the audience, one demonstration journey and which integrations belong in this iteration.
3. Use `3-prd` to define how the chosen data appears and how missing, stale or unavailable data behaves.
4. Use `4-spec` to choose sources, methods, dependencies and verification, including any externally dependent work.
5. Use `5-build` to implement and verify the reviewed plan in working steps.
6. Use `6-ship` to prepare the demonstrated result and truthful submission materials.

Research and file inspection can continue during planning. The skill stages and their reviews remain recorded in order.

## Primary references checked

- [Open-Meteo forecast documentation](https://open-meteo.com/en/docs) and [access/pricing terms](https://open-meteo.com/en/pricing).
- [WorldPop population-count product categories](https://hub.worldpop.org/project/categories?id=3) and [Global2 overview](https://www.worldpop.org/blog/worldpop-global2-global-high-resolution-population-estimates-for-2015-2030/). The local file still needs product-level verification.
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg).
- [USGS global elevation access](https://www.usgs.gov/faqs/where-can-i-get-global-elevation-data).
- [Earth Engine access requirements](https://developers.google.com/earth-engine/guides/access).
- [DHM real-time streamflow page](https://dhm.gov.np/hydrology/realtime-stream) and [DHM data page](https://dhm.gov.np/pages/data). An authorized API has not been established by this review.

Local evidence: `docs/data-catalog.md`, `docs/data-audit.md`, `backend/app/providers.py`, `backend/app/jobs.py`, and `backend/scripts/`.
