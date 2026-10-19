# Product requirements

Himalayan Sentinel helps citizens and local responders inspect flood/GLOF indicators without presenting experimental scores as official forecasts.

Public users need an understandable situation map, source freshness, lake baseline and score explanation, published safety notices, bilingual safety labels and a private image-report form. Administrators need moderation, provider diagnostics, account/jurisdiction assignment and audit history. Assigned government officials need evidence review, incident confirmation, a response checklist and a controlled alert lifecycle.

The primary success criterion is a demonstrated report-to-alert-to-resolution workflow with identity/location privacy, server authorization and clear simulation labels. Original lake data must remain unchanged, source ranks must remain independent of dynamic scores, and missing evidence must never imply safety. Provider failures must be explicit and recoverable.

The public UI keeps the existing light teal visual theme, Leaflet and Recharts. Forms have labelled controls, focus states, actionable errors and mobile layouts. Critical public safety labels have English/Nepali translation keys. Reduced-motion preferences are respected in new charts/transitions.

Verification includes deterministic API/security/import tests and browser workflows, plus TypeScript and production build checks. Remaining operational/data limitations are documented in README and docs/architecture.md. This plan records the current implementation scope; it does not establish the provenance of earlier planning documents.

The current integration requirements are in [devpost/prd.md](devpost/prd.md): a public/staff evidence explorer, separate broader lake and historical-event datasets, live forecast provenance, contextual district population and a district-evidence link in the existing reviewed-notice workflow.
