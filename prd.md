# Product Requirements Document

## Problem
Risk data is fragmented and often difficult for citizens and municipal teams to interpret quickly. Himalayan Sentinel turns several signals into a single explainable view without claiming to be an official forecast.

## Users
- Citizens checking nearby conditions
- Municipal staff preparing public notices
- Responders prioritizing situational awareness

## Core experience
On launch, users see a national situation summary and map. Selecting a marker updates the risk score, factor details, chart, explanation, and report form. Users can switch alert language and generate a shareable advisory.

## Functional requirements
1. Show all seeded regions and risk levels.
2. Compute risk with documented weights and fixed thresholds.
3. Display contributing factors and trend data.
4. Generate English and Nepali explanations/alerts containing a disclaimer.
5. Accept categorized community observations.
6. Work with seeded data when third-party APIs or keys are unavailable.

## Non-functional requirements
- Responsive at mobile and desktop widths
- Accessible labels and keyboard-operable controls
- No API keys committed to source
- Clear disclosure of mock data and limitations

## Metrics
Demo task completion, alert generation success, report submission success, and zero ambiguity that the prototype is not an official warning system.
