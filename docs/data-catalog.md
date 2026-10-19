# Data catalog

The existing root `data/` is the read-only raw-data location. It is intentionally not moved or overwritten. `backend/data/processed/` holds ignored, reproducible derivatives and the complete machine-readable audit; `backend/app/data/regions.json` remains the original regional demonstration fixture. No additional dataset was downloaded during implementation. Python/npm packages are development dependencies, not hazard datasets.

`scripts/inspect_datasets.py` recursively reads every original file, hashes bytes, opens each logical shapefile, GeoJSON, CSV, GeoTIFF, metadata XML and PDF. Binary `.dbf/.shx/.sbn/.sbx` sidecars are interpreted with their parent shape inventory or retained as index sidecars. The file-by-file size, record count, CRS and invalid-geometry summary is generated in [data-audit.md](data-audit.md); exact columns, source DBF types, missing counts, duplicates, errors, source metadata text and SHA-256 hashes are in `backend/data/processed/data-quality.json`. Run it again to reproduce. An error is recorded rather than hidden if a file cannot be opened.

## Potentially dangerous glacial lakes

Local package title: Potentially dangerous glacial lakes in the Koshi, Gandaki, and Karnali river basins of Nepal, the Tibet Autonomous Region of China, and India. Source ICIMOD, published 10 September 2020, based on the 2015 glacial lake inventory. Accompanying XML/PDF allows use with source attribution; it labels copyright rather than assigning a specific Creative Commons licence. General download agreement requires attribution, disclaims accuracy/liability, preserves ownership and prohibits charging for redistribution. It also requires respecting dataset-specific terms. No authentication or agreement acceptance was bypassed.

`PDGLs.shp` contains **47** polygon records: Nepal 21, China 25, India 1; WGS84 EPSG:4326 from its `.prj`. All source geometries are valid, no empty geometry, duplicate full record or missing field was found. Integer fields: Id, Elevation, PID. Float: Latitude, Longitude, Area. String: GL_ID, Basin, Sub_Basin, Type, VS_inspect, Rank, RID, Country. `GL_ID` is preserved as the stable source identifier; source Rank I/II/III remains the baseline classification, separate from monitoring priority. Area/elevation values are retained without guessing units absent a field-level definition. Raw attributes remain available in processed records.

All transboundary records are retained. Polygons identify lakes, **not inundation footprints**. Basin membership does not prove a specific downstream impact. This static inventory can support baseline prioritization, never a current event forecast.

Required attribution:

> ICIMOD. (2020). Potentially dangerous glacial lakes in the Koshi, Gandaki, and Karnali river basins of Nepal, the Tibet Autonomous Region of China, and India [Data set]. ICIMOD. https://doi.org/10.26066/RDS.1971950

Metadata: [ICIMOD PDGL record](https://rds.icimod.org/metadata/799aab42-e816-4e7d-87bb-8b2147eb6a1a).

## Broader glacial-lake inventory

`GL_3basins_2015.shp`: 3,624 polygons; Nepal 2,070, China 1,509, India 45. EPSG:4326; no invalid/empty geometries, duplicate full records or missing fields. Same first ten source fields as PDGL excluding inspection/rank/report IDs. Metadata describes Landsat 2015–2016 mapping and SRTM-derived attributes; actual delivered `.prj` is geographic WGS84 despite metadata mentioning UTM processing. Source CRS is read from `.prj`, never assumed from that narrative.

Published 10 September 2020; free use with attribution under the supplied metadata/general agreement. Citation: ICIMOD (2020), Glacial lakes in the Koshi, Gandaki, and Karnali river basins of Nepal, the Tibet Autonomous Region of China, and India, https://doi.org/10.26066/RDS.1971946. This inventory is now prepared by `scripts/import_context_data.py` and exposed as a separate searchable contextual layer. It is not mixed into PDGL monitoring or presented as equally hazardous.

## Historical GLOF database

High Mountain Asia; CSV revisions v1 (30 December 2022), v2 (13 December 2023), v3 (13 December 2024), v4 (13 December 2025). Counts: **697, 703, 736, 766**. Revisions overlap and must not be concatenated as independent observations. Latest metadata covers 1533–2025 and explicitly describes repeated events. No exact duplicate rows were found in each file; repeated lake events are legitimate events, not automatically duplicates.

All CSV cells load as strings to preserve approximations and missing markers; 60 columns describe event ID, dates, lake/glacier IDs, WGS84 coordinates, lake type/processes, downstream impacts, deaths/injuries, infrastructure, economic effects and source references. `Data Description.pdf` defines GF_ID as event identifier, lake coordinates as WGS84 decimal degrees (despite its INT format notation), elevation metres above sea level, area square metres, volume cubic metres, discharge cubic metres/second and economic damage USD. These definitions belong to this historical CSV, not the PDGL DBF.

Missingness is substantial: v4 lacks exact year in 181 records, day in 441, lake-area values in 727 and lowest-impact coordinates in 285. `NA`, empty values and unknown labels must not become zero; plus-suffixed values are approximate. Some non-UTF8 source characters decode with replacements and are flagged in the audit; source bytes are retained. This outcome inventory has no established negative examples or leakage-safe pre-event feature table. It does not justify supervised prediction.

Supplied metadata explicitly states **CC BY 4.0**. Attribution: ICIMOD. (2023). GLOF database of High Mountain Asia [Data set]. ICIMOD. https://doi.org/10.26066/RDS.1973283. Metadata [record](https://rds.icimod.org/metadata/8881454b-6f7c-461b-95c2-eaf7618230d9). The latest local revision is exposed as historical context through the evidence explorer; earlier overlapping revisions are not concatenated. Approximate dates and missing coordinates remain visible. No classifier is trained.

## Administrative boundaries

`data/GeoJson/provinces.json`: seven features; `districts.json`: 77. Valid, nonempty polygons; property schemas, nulls and duplicate counts are recorded in the audit. District attributes include DISTRICT, Province, OBJECTID and shape summary fields. Province features contain additional demographic/economic fields with unverified provenance/definitions; those attributes are not used as current exposure measurements. Boundary currency/date, original licence and provenance are **verification required**. ICIMOD NepalAdmin service URLs supplied in the brief are a provenance lead, not proof the local files came from that service. Coordinates follow GeoJSON longitude/latitude convention; audit records any declared CRS. Used for local map context, not to certify emergency jurisdiction boundaries. Do not republish raw boundaries until terms are confirmed.

## Population raster

`npl_pop_2026_CN_100m_R2025A_v1.tif`: 32,079,831 bytes, EPSG:4326, 9,773 × 4,921 cells. TIFF tags identify NPL population 2026, WorldPop R2025A v1, generated 4 August 2025; copyright tag **CC-BY-4.0**, NoData **-99999**. It is a static modelled population estimate for 2026, not a live census or exact count. Bands, dtype, resolution and bounds are recorded in the audit. Whole-raster cell-level missingness has not been scanned; the NoData marker is recorded. Duplicate rows/geometry validity are not meaningful raster-record checks. The exact local product tags and the official [WorldPop R2025A v1 release statement](https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf) identify this as population counts per grid cell, with alpha-release uncertainty. The evidence explorer now sums valid pixel-centre counts within selected district boundaries using bounded windows and source-keyed caches. No density multiplier is applied; no downstream exposure total is inferred. The API rejects mismatching product metadata before numerical aggregation.

## Runtime providers and fixtures

- **Open-Meteo:** enabled by the current example configuration; live daily precipitation and maximum temperature forecast, timeout/retry/cache/response validation and explicit stale/demo fallback. CC BY 4.0 attribution shown; review [API terms](https://open-meteo.com/en/terms) before commercial deployment. First day is a calendar-day total, not a rolling next-24-hours observation. Regional and offline forecasts are labelled simulated.
- **OpenStreetMap:** map tiles only, © OpenStreetMap contributors attribution in both maps. Respect [tile usage policy](https://operations.osmfoundation.org/policies/tiles/); no bulk download or excessive Overpass calls. Infrastructure exposure is unavailable.
- **DHM:** interface only; no authorized API and no scraping. **SRTM, GPM, JRC/OPERA/HLS/Earth Engine:** provider interfaces/unavailable state; no downloaded raster or authenticated ingestion. **WorldPop:** modelled district population context is available after exact-product verification; flood exposure remains unknown without an impact footprint.
- **Citizen evidence:** user consent, private original and EXIF-free JPEG derivative, restricted staff access, short status-only tracking response. No public image or identity feed.
- **Synthetic scenario:** explicitly marked simulated rain on an actual inventory Rank I lake; no fabricated authoritative rank or observation. The existing eight-region fixture is fully simulated for trend and UI demonstration.

## Reproduction and integrity

Run inspection → preprocessing → import as documented in README. Invalid polygons or duplicate source IDs stop the import; source geometries are never silently repaired. The importer performs idempotent source-ID upserts, retains raw properties and attribution, and fills PostGIS geometry/GIST indexes when PostgreSQL is selected. Small development subsets are generated in the ignored processed directory. Audit hashes can be compared after implementation to confirm raw-byte preservation.
