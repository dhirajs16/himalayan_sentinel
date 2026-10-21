# Submission preparation - 21 October 2026

Video work is explicitly deferred. This entry is not confirmed submission-ready.

| Step | State | Evidence / remaining action |
|---|---|---|
| 1. Hands-on review and learning | Partial; learner response needed | Earlier screenshot establishes evidence-page access. District/search interaction, the complete report-to-resolution journey, learning wrap-up and readiness sign-off remain unconfirmed. A WorldPop -> API -> population-panel walkthrough is recommended; no experience or reflection is invented. |
| 2. Dataset rights and integrity | Runtime boundary issue resolved | Pinned Open Knowledge Nepal CC BY 4.0 bundle with attribution/license and unchanged upstream bytes. All 33 original raw-data hashes and both bundled boundary hashes match. Original unverified boundaries remain excluded and unused. See `../docs/data-catalog.md`. |
| 3. Repository handoff | Local preparation; publication requires authorization | Origin: `https://github.com/dhirajs16/himalayan_sentinel.git`. Unauthenticated GitHub API returned 404 on 21 October; public access is unverified. No push or visibility change performed. See `../docs/repository-handoff.md` for included/excluded files and audit scope. |
| 4. Demo video | Deferred by entrant | No recorder run or upload. Handoff-mentioned footage is now missing and may have been removed by default test-output cleanup; no other copy was found in checked artifact folders. Routine output is now separate (`test-results/e2e`). No replacement recording; see `../docs/demo-checklist.md`. |
| 5. Devpost fields | Public requirements rechecked; actual form unavailable | Public update confirms repository in Try it out, Skill Pack usage explanation and age-of-majority checkbox. Exact live form and exit-survey fields remain unverified. Entrant writes final answers; legacy assistant draft stays local and ignored. Nothing submitted. |
| 6. Skill Pack timing | Adverse public guidance found; no project-specific exception | Manager says use the pack from the beginning. Recorded initial prototype predates pack installation. The later combined-commit permission in that thread addresses a different participant/question. No organizer message sent. See `../docs/organizer-clarification.md`. |

## Fresh technical verification

- Default `pytest -q` initially failed while discovering inaccessible ignored runtime directories. Added `testpaths = ["tests"]` to the pytest configuration.
- After the correction: **45/45 SQLite tests pass** and **45/45 PostgreSQL/PostGIS tests pass**, using isolated temporary databases/schemas and evidence storage. One existing FastAPI/Starlette test-client deprecation warning remains.
- Python Ruff lint and formatting pass (31 files); mypy passes (21 source files).
- Production frontend build and standalone TypeScript checks pass. The first overlapping build/browser attempt timed out during frontend startup. A sequential retry passes **all nine browser tests** and exits zero after scoped cleanup of its verified Windows test services. The browser-generated Next.js type reference was restored to its original production path; standalone typing passes afterward. Routine test output was then separated from deferred recordings; configuration/test discovery was checked without running the recorder.
- Prepared context: 3,624 broader lakes, 766 historical events and 77 districts. Rasuwa: 46,137.78 modelled people / 19,614 valid cells. Gorkha: 248,736.68 / 96,431 valid cells. These are district context, not flood exposure.
- All 33 raw-data hashes match the prior audit; both pinned boundary hashes match the bundle manifest. Source files were not changed.
- Actual Rasuwa weather refresh succeeds with `mode: live`, `freshness: fresh`, retrieval **2026-10-21 07:06:27 UTC / 12:51:27 Nepal time**, source date 21 October. The initial sandbox network attempt returned a correctly labelled stale cache; the authorized network-enabled retry fetched current data. Recheck before a later demonstration; this timestamp is not a promise of continued freshness.

## Publication audit

Reviewed four reachable local commits, 176 distinct historical blobs and 118 historical paths, plus working files and intended additions. The final index contains 131 files, with no excluded private/raw/editor paths or credential/token matches; staged boundary hashes match and the whitespace check passes. No matched private database credential, private-key/provider-token pattern or private/raw-storage path was found in the reviewed publication material/history. Generic matches were example settings or code expressions, manually classified. This is a scoped check, not a universal secret-detection guarantee. The profile, `.env`, raw data, evidence, generated files and legacy assistant draft stay excluded; unrelated editor settings stay outside the commit. Docker context exclusions were tightened; Docker images were not rebuilt. Details: `../docs/repository-handoff.md`.

## External checks and remaining decisions

The current overview and organizer update still display **26 October 2026, 17:00 EDT = 27 October 2026, 02:45 Nepal time**. The full rules returned HTTP 403; their complete current text was not reverified. Source links and confirmed public form requirements are in `../docs/hackathon-compliance.md`.

Required actions remain: actual learner review/wrap-up/sign-off; a project-specific eligibility decision if pursuing this entry despite public timing guidance; explicit authorization before publishing code/history; signed-out verification of the published commit; entrant-written answers and exit survey in the actual form; eventual reviewed public video link; and explicit authorization before submission. No final submission, eligibility approval or personal confirmation is inferred.
