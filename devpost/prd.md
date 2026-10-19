---
doc: prd
status: approved
---

# Himalayan Sentinel — Product Requirements

## Authorization

Derived from the displayed scope and the learner's instruction to complete the entire project. Detailed choices below are agent decisions under that delegation, not fabricated interview answers or a claim that the learner personally reviewed unseen screens.

## The Core Journey

Implements `scope.md > The Core Loop`. A responder opens the public dashboard, explores real geographic context and source dates, checks a selected district's forecast, then uses the existing citizen-report, moderation, confirmation and alert-review workflow. The resident sees a time-bounded demo notice. Contextual data never authorizes publication automatically.

## Evidence Explorer

Implements `scope.md > The POC Boundary`. Add a public evidence section accessible from staff monitoring too. A district selector coordinates current weather and population context. The broader glacial-lake layer and historical GLOF records have their own searchable, paginated lists and map layers. Search supports country and basin; district filtering uses actual point/polygon containment rather than treating a basin as an inundation zone. Records without usable coordinates remain discoverable in lists and are identified as unmapped. Static inventory dates and historical coverage are visible. Dangerous-lake ranks remain exclusive to their original source.

Acceptance: locally present inventory and latest historical revision are reproducibly prepared and exposed by the API; pagination totals and map results agree with filters; earlier historical revisions are not counted again. Selecting a record reveals retained attributes, source IDs and attribution. Missing inputs produce a useful empty state.

## Current Weather

Implements `scope.md > What "Working" Looks Like`. Selecting a district loads its daily forecast. Display retrieval/source time, live/cached/simulated mode, freshness, rainfall and maximum temperature with accessible values. A failure keeps an explicit error/fallback state. Forecast rainfall is not labelled observed river flow or a forecast of a GLOF.

Acceptance: demonstrate a real successful fetch where the provider is reachable, verify caching and failure behavior, and provide a live synchronization command. Bound concurrency, honor provider throttling and avoid duplicating requests on each render. Persist successful observations; simulated fixtures never become credible cached observations. Disabled providers do not silently return fresh live data.

## Population Context

Implements `scope.md > The POC Boundary`. Show a modelled population estimate for the selected district, with product year, units, covered cells and geographic scope. Explain that the district total is contextual and is not a count of people exposed to a flood. Verify the exact local WorldPop release before numerical integration; mask NoData and use bounded raster windows. Errors and missing boundaries/raster remain explicit.

## Evidence to Notice

Implements `scope.md > The Unique Kernel`. Staff monitoring can inspect the same evidence. During alert composition, show an accessible route to district context; staff explicitly decide which facts to include in the existing evidence summary. No automatic causal association between a lake and an incident is created. Existing server authorization, approval invalidation, publication/version history and private evidence access remain enforced.

## Look and Feel

Carry forward the existing light teal palette, readable type, bordered cards and responsive staff shell. Use clear data labels rather than decorative risk counters. Provide labels, focus indicators, loading/error text, keyboard controls, mobile layouts and a textual equivalent to maps/charts. This is an agent continuation of the existing design under delegated implementation authority.

## States and Boundaries

Loading and failure states are visible per source. Stale observations retain timestamps. Empty datasets show installation guidance in technical setup docs and a plain unavailable message in the product. Only validated coordinates appear on the map; partial dates and missing impact values remain unknown. External terrain, satellite, hydrology and infrastructure integrations remain tracked follow-on work where required access/methods are not established. Public notices remain demonstration notices.

## Product Decisions

Reuse the current dashboard and operations routes. Keep broader inventory/historical context separate from the assessed dangerous-lake database to avoid inventing ranks or associations. Show bounded result pages rather than rendering thousands of polygons at once. Build a useful district context view before adding externally dependent sources. These are agent implementation decisions under the learner's explicit completion request.

## Verification and Open Questions

Verify imports, filtering, date/coordinate/NoData handling, source modes and existing publication protections through isolated backend tests. Verify search, district selection, weather/population states, mobile overflow and the full existing report-to-public-notice journey in browser tests. External source access and operational scientific validation remain limitations, not prerequisites for demonstrating the reviewed scope.
