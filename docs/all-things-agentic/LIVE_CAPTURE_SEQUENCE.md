# Live, unedited Proof of Action sequence

This sequence is designed for one reproducible capture against the real deployed product. It does not fabricate timestamps or replay cached UI.

## Target

<https://studiogrid-web-729921508335.europe-west3.run.app>

No localhost. Use English for the primary take.

## Before recording

1. Confirm the URL returns HTTP 200.
2. Confirm unauthenticated Control API and Tool Server requests return 401/403.
3. Open the public dashboard and verify all four runtime cards say `CONNECTED`.
4. Prepare sanitized read-only cloud views; do not change IAM, revisions, or resources.
5. Click **Reset Demo** once and wait for the clean state.
6. Start screen recording before the actor-delay click.

## Continuous action segment

1. Keep the `.run.app` address bar visible.
2. Select **Maya Reed — ACT_02**.
3. Click **Simulate delay — 45 min** once.
4. Keep the recording continuous while “running” is visible. Do not edit out latency.
5. When the result appears, show:
   - FACT actor/delay event;
   - PENDING proposal;
   - reason and concrete scene reorder;
   - evidence, expected benefit, risks, confidence;
   - agent/model/execution/correlation/tool metadata.
6. Point out that the schedule has not changed yet.
7. Show the human-only authority label.
8. Click **Approve as human** once.
9. Show the APPROVED state, schedule before/after, and `HUMAN_DECISION` timeline item.
10. Refresh the page and show that the same decision and schedule persist.
11. Click **Coverage Check** once.
12. Show planned/completed facts, OPEN alert, and missing `SH_12`/`SH_13`.

## Cloud proof segment

Show only read-only, sanitized views:

1. Vertex AI Agent Engine resource:
   `projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`
2. Cloud Run services in `europe-west3`:
   - `studiogrid-web` — public;
   - `studiogrid-control-api` — private;
   - `studiogrid-tool-server` — private.
3. Firestore proposal/execution/event evidence matching the live flow.
4. Optional sampled Cloud Trace view, with messages and sensitive attributes hidden.

## After recording

1. Run a final **Reset Demo** to return the synthetic public experience to a clean state.
2. Do not delete proposal, execution, event, or Agent Engine evidence.
3. Verify the captured identifiers match one coherent execution.
4. Inspect every frame around cloud-console transitions for account/email/token exposure.
5. Record the capture date, public web revision, Control API revision, and Agent Engine resource in the video notes.

## Expected assertions

| Assertion | Expected |
|---|---|
| Public root | 200 and redirects/renders `/en/dashboard` |
| Control API without identity | 401/403 |
| Tool Server without identity | 401/403 |
| ACT_02 result | PENDING proposal from Schedule Agent |
| Schedule before approval | unchanged |
| Human approve | APPROVED and reordered schedule |
| Refresh | persisted state |
| Coverage | OPEN alert, missing `SH_12`, `SH_13` |
| Final reset | synthetic seed restored |
