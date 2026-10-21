# Integrated demonstration checks

Video work is deferred by the entrant's instruction on 21 October 2026. Do not run the recorder, edit footage or upload it during the remaining technical preparation. Existing local footage has not been accepted as a reviewed submission video.

The handoff-mentioned capture under `frontend/test-results/demo/` was not found
after the preparation tests. The original default Playwright output cleanup may
have removed it; no other WebM copy was found in the checked repository output
and temporary Playwright artifact folders. Routine output is now explicitly
`test-results/e2e`, a sibling of `test-results/demo`, to prevent this collision.
No replacement recording was made; video remains deferred.

The following is a technical reference for later recording. The [event overview](https://learn-ai-basics.devpost.com/?ref_medium=portfolio) currently requests a 1-3 minute working demonstration; confirm the actual form's constraints before recording. The entrant writes their own narration and personal reflections.

## Automated local footage (for later use)

From `frontend`, run `npx playwright install ffmpeg` once, then `npm run demo:record`.
The recorder starts temporary services on 8010/3100 with an isolated SQLite database,
public example accounts, staged evidence and mock delivery. It captures a 1440×900
WebM under ignored `frontend/test-results/demo/`. It never publishes a notice in
the working PostgreSQL database. Other local data is read through the actual APIs;
weather in this recording environment is explicitly simulated. The footage has no
spoken narration or music. Review it, supply your own explanation if desired, and
upload the reviewed video publicly to YouTube/Vimeo. Local footage alone is not a
submission video link. Setup/authentication pauses can be trimmed; retain the
visible review, approval, publication and resolution steps.

The script is `frontend/demo/record.spec.ts`; the separate recording configuration
keeps this optional capture out of the ordinary browser test suite.

## Preparation

1. Start the app with `./scripts/dev.ps1` after installing dependencies. Confirm the context importer reports 3,624 lakes, 766 historical records and 77 districts when the supplied local files are present.
2. From `backend`, run `.venv/Scripts/python.exe -m app.scripts.sync_weather --district rasuwa` and require `mode: live` with a recent retrieval time before describing weather as live.
3. Open `/evidence?district=rasuwa`. Verify a real source record, source dates, forecast and modelled district population. Use a district with records for a district-specific historical search; an empty result is not a current safety assessment.
4. Keep credentials, unrelated windows and private evidence out of the recording. Use the documented local demo accounts and a clearly staged report image.

## Visible sequence

- Open district evidence, inspect a lake/event source record and its retained attribution. Identify the static/historical coverage.
- Show the selected district's actual forecast mode and retrieval time, and the population panel's contextual scope.
- Submit a staged citizen observation. Have an administrator inspect and escalate it.
- Have the assigned government account confirm the incident. Open its district evidence link and inspect facts before choosing what to include in the notice.
- Save, submit, approve and publish a clearly marked demo notice. Show it on the public dashboard and its effective/expiry times.
- Resolve the notice and check the public view updates. No real SMS/email is delivered by the mock adapters.

Cut setup and typing pauses from the final recording. Do not present the staged report as an observation from a historical flood, claim a lake caused it without evidence, or assign prevented casualties to this prototype. Motivation references are in `motivation-and-evidence.md`.

## Submission items still supplied by the entrant

- Public YouTube/Vimeo video URL, checked without signing in.
- Public code repository URL with the current source, planning documents, setup instructions and license. Verify dataset rights before including datasets; keep private context and credentials excluded.
- Your own project description, learning reflection, Skill Pack usage explanation and other current form fields.
- Personal eligibility confirmation and final Devpost submission.

Local code verification and screenshots do not establish that these external submission actions have occurred.
