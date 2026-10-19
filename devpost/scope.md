---
doc: scope
status: approved
---

# Himalayan Sentinel — Evidence to Reviewed Notice

A decision-support application that brings Nepal's flood-related geographic data, current forecasts and citizen evidence into one review workflow, helping a local responder prepare an understandable public notice.

## The Unique Kernel

A responder can trace the evidence behind a notice: its source, applicable time, missing inputs and human review. Each integration should help the responder make a concrete decision. The demonstration's finish line is a useful evidence-to-notice journey.

## Who It's For

Primary user: a local-government disaster-response officer serving a flood-prone district such as Rasuwa or Gorkha, who needs to inspect relevant evidence and prepare a reviewed notice.

Supporting users: residents submitting private observations and reading notices, and administrators moderating incoming reports. Government adoption and authority are not established; no user interviews or observed workplace processes are claimed.

This audience is an agent recommendation under the learner's instruction to choose planning answers, presented for review.

## The Core Loop

Open a district or basin → inspect relevant lakes, available historical events and current forecast data → check freshness, coverage and missing inputs → review a citizen observation → confirm an incident through the existing staff workflow → draft, review and publish a clearly marked demo notice → show the notice publicly and resolve it when appropriate.

District or basin context must not imply an established upstream/downstream hazard relationship. Contextual population counts must not be labelled as people exposed to flooding.

## Inspiration & Identity

The learner identified recent floods in Rasuwa and Gorkha as the motivation: useful information needs to reach the people who can act on it. The current map, light teal identity and staff workspaces are the starting point. The proposed tone is calm, readable and specific about evidence and uncertainty.

Official event references and the prime minister's UN address are recorded in [Motivation and evidence](../docs/motivation-and-evidence.md). These are distinct events and statements; neither establishes this prototype's ability to predict or prevent them.

## Why This Matters to the Learner

The learner wants a useful response to those disasters and a competitive hackathon demonstration. Their adopted learning goal is to connect real geographic datasets and live weather, verify them, distinguish measured, simulated and unavailable information, and demonstrate how evidence supports a reviewed public notice.

## What "Working" Looks Like

In a short recorded journey, a responder opens a Nepal district or basin, sees real imported inventory and historical records where coverage exists, checks a successfully retrieved and timestamped weather forecast, and reviews a deliberately staged citizen report. They prepare and publish a demo notice; a resident sees it with its validity and instructions.

The visible proof is a traceable evidence-to-notice journey. Source records can be inspected, unavailable inputs remain labelled, and failed requests are never presented as live data. Staged reports are marked as demonstrations, not evidence about a real historical disaster.

## The POC Boundary

Proposed implementation order for this iteration:

1. Integrate the available broader lake inventory and latest historical GLOF revision as distinguishable geographic context, preserving existing dangerous-lake ranks and source attribution.
2. Enable and verify live weather, persist freshness and failure states, and make the forecast relevant to the selected location. Forecast rainfall remains distinct from observations.
3. Use the WorldPop raster for labelled population context after verifying units, coverage and NoData. Downstream exposure is not claimed without a validated hazard footprint.
4. Connect relevant evidence to the existing review/publication journey with clear sources, geographic relevance and readable notices. Supporting contextual layers need not all appear in the short demo.

The learner requested all integrations. Track terrain, satellite water/change, satellite rainfall, DHM observations and infrastructure as follow-on integrations with explicit access and method requirements. Promote a source into the demonstrated version when a useful end-to-end path and verification are available. The technical plan must define acquisition routes before implementation; an unavailable adapter does not count as completed integration.

## Later

- Terrain and satellite analysis after obtaining suitable data and defining comparisons and quality checks.
- DHM observations after verifying an authorized feed or supplied exports and station metadata.
- Satellite rainfall and infrastructure layers after choosing acquisition routes, spatial relevance, refresh policies and verification.
- Operational delivery/adoption after authority, identity, notification and reliability requirements are established.

These are proposed sequencing choices, not cancellation of the broader integration goal or a claim that external dependencies are already available.

## Explicitly Cut

- Quantified claims that this prototype would have saved lives in the motivating events: no counterfactual evaluation supports them.
- Autonomous emergency publication, real public warning authority and guaranteed lead time: retain human review and local demo notices.
- Validated disaster prediction, evacuation routing and affected-population totals: the required methods and hazard footprints are not established.
- Synthetic measurements presented as live data: source modes and missingness remain visible.

## Session Provenance

Prepared 19 October 2026 for further development of an existing application. The learner authorized this displayed scope by instructing the agent to complete the entire project following the instructions. New technical details are agent implementation choices under that delegation. No earlier Skill Pack history or submission eligibility is asserted.
