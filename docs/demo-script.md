# Three-minute demonstration

Use two browser contexts (public and staff). Pause the scheduler during the controlled rainfall scenario so it does not replace deliberately simulated inputs. All alert publications are local demo notices; mock SMS/email sends no messages.

Preparation: copy `.env.example` to `.env`, migrate, seed, import the local PDGL data. Run `python -m app.scripts.demo_scenario --phase baseline` from backend, then start both applications. Have a small local photograph ready without sensitive personal details. Follow the dashboard's selected demo district for the report.

1. **0:00–0:25** Show the light teal public dashboard, disclaimer and real ICIMOD polygons. Filter Nepal, open the Rank I lake identified by the scenario command. Point out static baseline, missing exposure data and prototype confidence.
2. **0:25–0:45** Run `python -m app.scripts.demo_scenario --phase rainfall`. Reload the profile: synthetic rainfall increases priority from 35 to 65 while Rank I remains unchanged. Show contributions, simulated weather charts and assessment timeline. This is a demonstration, not a forecast.
3. **0:45–1:10** Public report form: category river rise, selected district, description, entered/GPS coordinates, current observation time and image. Check consent, accuracy and demo-verification declarations. Submit and save tracking code.
4. **1:10–1:30** Sign in as administrator, inspect sanitized private evidence, enter review reason and escalate. Administrators have no official publication controls.
5. **1:30–1:55** Sign out; sign in as government official. Review the escalated evidence and monitoring page, enter reason, confirm incident. Open Incidents; inspect response checklist and compose an alert.
6. **1:55–2:25** Request an AI-assisted draft (Gemini if configured, labelled template otherwise). Edit description/safety instructions, set expiry, save draft. In Alerts: submit → approve → publish; confirm each consequential decision.
7. **2:25–2:45** Public dashboard refreshes within 15 seconds and displays DEMO publication with safety instructions. Admin delivery log shows three mock deliveries. No real SMS/email was sent.
8. **2:45–2:58** Government resolves the alert and closes the incident; public notice disappears. Export summary and show version/audit history. Explain missing terrain, impact footprint, population modelling and scientific validation.

Record under three minutes for the official submission recommendation; remove setup/typing pauses from the video. Public YouTube/Vimeo upload and Devpost entry are separate user actions, not performed by this implementation.
