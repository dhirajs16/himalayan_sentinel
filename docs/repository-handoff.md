# Repository handoff - 21 October 2026

This records technical preparation, not publication, eligibility approval or a
Devpost submission. Video recording, editing and upload remain deferred.

## Included work

- Pinned Open Knowledge Nepal CC BY 4.0 district/province boundaries, manifest,
  license notice and unchanged upstream bytes. Runtime routes, context filtering,
  spatial imports and modelled population use this bundle and display attribution.
- Existing submission preparation records and optional recorder source. The
  recorder was reviewed as source only; it was not run in this session.
- Pytest discovery restricted to `tests/`. The default command previously tried
  to enter inaccessible ignored `backend/var/sentinel-e2e-*` directories and
  failed before running tests. Both backend suites pass with this correction.
- Publication records distinguish automated checks, actual learner participation,
  legacy assistant text and the public organizer's timing guidance.
- Routine Playwright output is now `test-results/e2e`, separate from the recorder's
  `test-results/demo`. The previous shared parent allowed normal test cleanup to
  remove deferred footage. The handoff-mentioned capture is currently missing
  and may have been removed by that cleanup; no other copy was found in the
  checked output/temporary Playwright artifact folders. No recorder was run to
  replace it; video remains deferred.

## Privacy, history and data audit

Before the preparation commit, all four reachable local commits were inspected:
176 distinct historical blobs across 118 historical paths. Tracked working files
and intended additions were reviewed too. Checks covered private/raw-storage paths,
private keys, common provider-token formats, credential assignments and database
URLs; the actual private database URL and decoded password were compared without
printing them. No private credential match or private/raw-storage path was found
in the reviewed files or reachable history. Generic matches were inspected and
were empty settings, code expressions, environment substitutions, example accounts
or documented local demonstration passwords. This is a scoped repository audit,
not a guarantee against every possible secret format or inaccessible remote ref.

All 33 original data-file SHA-256 hashes match the saved audit. Both bundled
boundary SHA-256 hashes match their manifest. The only tracked report-image fixture
is a 12-by-12 PNG with no EXIF entries; private report images and database storage
remain ignored. Dataset notices accompany the boundary bundle; other raw datasets
remain local and excluded. Source permissions and remaining interpretation limits
are documented in [data-catalog.md](data-catalog.md).

Root/backend/frontend example environment files contain public local demonstration
settings, not deployment credentials. `.gitignore` excludes private environments,
the learner profile, raw data, evidence storage, test artifacts and the legacy
assistant-written submission draft. Docker context exclusions cover `.env.*`, the
profile/draft and development build output too. Docker images were not rebuilt.
The unrelated `.vscode/settings.json` remains outside the preparation commit.
Normal Git author metadata accompanies any published history.

The final staged-tree audit covers 131 indexed files: no matched private database
credential or key/token pattern, no excluded private/raw/editor path, and both
staged boundary hashes match the manifest. A staged whitespace check also passes.

## External checks and authorization

An unauthenticated GitHub API request for
`https://github.com/dhirajs16/himalayan_sentinel` returned **404** on 21 October.
That does not establish public access. A later authorized push on 21 October
advanced remote `main` from `15e1e1d` to reviewed commit
`1ad4ee09ca22e0f69a996f82acea9db6190d77a8`; authenticated `ls-remote` verifies both
HEAD and main at that exact commit. Signed-out repository API, commit API and
GitHub webpage requests all still return 404 after the push.

After explicit authorization to push or change visibility, check the intended
branch and its diff, publish the reviewed commit, then verify that exact commit
and required files without authentication. Publishing exposes committed code,
assets and included history. The user explicitly authorized the push of `1ad4ee0`
only; the normal non-force push succeeded. No visibility change, deployment,
message to an organizer or Devpost submission was performed. Later documentation
edits remain local, outside that authorized push. The user reconfirmed video work
is for later; no recorder was run.

## Remaining learner/submission work

1. Try district selection/search and the private-report-to-resolution journey;
   report observed behavior and any confusing step. Automated success does not
   establish that the learner performed these actions.
2. Complete the learning activity and final readiness confirmation. A recommended
   reference route is WorldPop product validation -> district pixel sum -> public
   context API -> population panel. Explain why district population is not flood
   exposure in the learner's own words; no personal reflection is supplied here.
3. Address the manager's [public late-adoption guidance](https://learn-ai-basics.devpost.com/forum_topics/45533-subject-eligibility-question-using-learn-skill-pack-after-initial-development).
   A project-specific exception is not confirmed; see
   [organizer-clarification.md](organizer-clarification.md). The later combined-commit
   permission in that thread does not override the timing reply.
4. Author final project answers and personal reflections, check every required
   field and complete the exit survey in the authenticated Devpost form. Public
   guidance confirms the repository in **Try it out**, Skill Pack usage explanation
   and age-of-majority checkbox. The complete live form was not accessible here.
5. Resume video work only when requested; supply and verify an accessible video
   link before submission. Deployment and peer feedback are optional.

The current public overview/update display a deadline of 26 October at 17:00 EDT,
equivalent to **27 October 2026 at 02:45 Nepal time**. The full rules returned HTTP
403 in this session; the current complete rules and form still need a final check.
See [hackathon-compliance.md](hackathon-compliance.md) and
[submission status](../devpost/submission-status.md) for source links and results.
