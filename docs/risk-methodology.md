# Monitoring methodology

This is an automated risk assessment and decision-support system. `lake-rules-1.0` is a transparent prototype, not a calibrated probability, flood model or scientifically validated prediction. A high monitoring priority recommends review; it does not establish an imminent event.

Each observed component is normalized to 0–100, then multiplied by its weight. Contributions sum to the 0–100 monitoring score. Unknown components contribute zero **and remain visibly unknown**, reducing completeness. Do not interpret a low score with missing evidence as evidence of safety.

| Component | Maximum contribution | Available evidence |
|---|---:|---|
| Baseline hazard | 35 | ICIMOD rank I → 100; II → 65; III → 35; unrecognized → unknown |
| Forecast rainfall | 20 | First forecast calendar-day precipitation / 150 mm, capped at 100 |
| Recent accumulated rainfall | 10 | Accumulation / 150 mm, capped at 100; unknown unless supplied |
| Temperature/snowmelt | 5 | Unknown; temperature alone cannot establish snowmelt |
| Lake-area change | 5 | Unknown without comparable observations |
| Terrain | 5 | Unknown without terrain analysis |
| Population exposure | 8 | Unknown without a downstream footprint and population overlay |
| Infrastructure exposure | 2 | Unknown without verified inventory and impact footprint |
| Verified reports | 5 | Unknown until a defensible spatial lake/report association is established |
| Official observations | 5 | Unknown until an authorized compatible observation is available |

The 150 mm normalization and all weights are arbitrary prototype choices requiring Nepal-specific expert validation. The scheduler uses only available forecast rainfall for the current Nepal calendar day and source rank. A stale forecast without that date leaves rainfall unknown. It does not infer a lake/report relation from the nearest district, count unverified reports, or turn total district population into downstream exposure.

Default intervals: Low ≤25, Moderate >25–50, High >50–75, Critical >75–100. Admin changes affect future recalculations and are stored with each assessment. Published alerts require official review regardless of any score. Baseline rank is always preserved independently of the monitoring interval.

Completeness is the sum of weights for available components. Evidence confidence equals completeness, capped at 25 for simulated data and 40 for stale observations. This heuristic describes evidence coverage, not statistical confidence or event probability. Freshness and observation timestamps render separately. Static ICIMOD ranks are not live hazard feeds.

The original district demo retains its five-factor formula for comparison (rainfall 30%, river 25%, glacial context 20%, seeded community signal 15%, seeded exposure 10%). Its values, counts, trends, exposure and classifications are labelled simulated. It is separate from imported lake assessments and never drives official publication.

Historical GLOF CSVs contain known events, incomplete dates, repeated events and no established negative population. No proof of temporally prior predictive features exists. A supervised classifier would introduce sampling bias/leakage, so no ML model is trained. Future research needs documented negatives, time-safe features, grouped temporal holdouts, imbalance-aware metrics, calibration and independent validation.

AI explanations receive structured stored facts and evidence IDs, cannot set a score or confirm an incident, and always remain drafts. Pydantic checks structured model output; unsupported evidence references or numerical prose are rejected in favor of a deterministic template. Safety actions come from approved fixed text. Human review remains essential for prose accuracy.

District WorldPop context is now available through the separate evidence explorer. It is not automatically injected into the population exposure score, which still requires a defensible downstream hazard footprint. Broader unranked inventory lakes and historical events are context, not additional assessed PDGLs.
