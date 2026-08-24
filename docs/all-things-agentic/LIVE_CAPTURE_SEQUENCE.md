# Live, unedited Proof of Action sequence

This sequence matches the current one-input production UI and the real deployed product. It does not use removed direct-action controls, fabricate timestamps, or replay cached results.

## Target

<https://studiogrid-web-729921508335.europe-west3.run.app>

No localhost. Use English for the primary take.

## Before recording

1. Confirm the public URL returns HTTP 200.
2. Confirm unauthenticated Control API and Tool Server requests return 401/403.
3. Prepare sanitized read-only Agent Engine, Cloud Run, and Firestore views.
4. Click **Reset Demo** and wait for the unified empty workspace.
5. Confirm there is no active Coverage result or PENDING/APPROVED Schedule proposal.
6. Start recording before submitting the first command.

## Continuous Taskmaster segment — Coverage first

1. Keep the `.run.app` address bar visible.
2. In **What happened or what needs to be done?**, enter:

   `Check SC_05 and make sure all required coverage is complete.`

3. Click **Run** once.
4. Keep the recording continuous while the real cloud workflow runs. Do not cut, accelerate, or hide latency.
5. When the contextual result appears, show:
   - route `CHECK_COVERAGE` and target `COVERAGE_AGENT` inside Technical details;
   - scene `SC_05`;
   - `1/3` completed shots and `33.3%`;
   - missing `SH_12` and `SH_13`;
   - `OPEN` alert;
   - Agent Engine, Gemini, private Tool Server, and Firestore `CONNECTED`;
   - model and real execution ID.
6. Say explicitly that no additional user step was required after the command.

## Continuous secondary segment — Schedule authority boundary

1. Click **Reset Demo** and confirm the Coverage result clears.
2. Enter:

   `Maya Reed is 45 minutes late. Keep today's shoot on schedule.`

3. Click **Run** once and retain the real loading state.
4. Show:
   - the Maya / 45-minute FACT;
   - PENDING recommendation;
   - proposed order;
   - evidence, affected scenes, expected benefit, risks, and confidence;
   - current schedule explicitly unchanged;
   - **Approve as human** / **Reject as human**;
   - the statement that the agent cannot make this decision;
   - `SCHEDULE_AGENT`, model, and execution ID inside Technical details.
5. Explain that routing, analysis, tool execution, and persistence are complete. The optional human action transfers authority only for the consequential mutation.
6. If the take includes approval, click **Approve as human** once, then show before/after, `HUMAN_DECISION`, and refresh persistence. Otherwise stop at PENDING and do not imply that the schedule changed.

## Cloud proof segment

Show only read-only, sanitized views:

1. Vertex AI Agent Engine resource:
   `projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`
2. Cloud Run services in `europe-west3`:
   - `studiogrid-web` — public;
   - `studiogrid-control-api` — private;
   - `studiogrid-tool-server` — private.
3. Firestore alert/proposal/execution evidence matching the live flow.
4. The architecture diagram, emphasizing:
   - natural language stops at the tool-less Gemini Command Router;
   - strict typed validation precedes Agent Engine;
   - Schedule and Coverage receive typed context only;
   - human authority is a separate path.

## After recording

1. Run a final **Reset Demo** so the public synthetic workspace is clean.
2. Do not delete proposal, alert, execution, event, or Agent Engine evidence.
3. Verify captured identifiers match the executions shown on screen.
4. Inspect cloud-console frames for account/email/token exposure.
5. Record the capture date, public web revision, Control API revision, and Agent Engine resource in the video notes.

## Expected assertions

| Assertion | Expected |
|---|---|
| Public root | HTTP 200 and English dashboard renders |
| Control API without identity | 401/403 |
| Tool Server without identity | 401/403 |
| Coverage route | `CHECK_COVERAGE` → `COVERAGE_AGENT` |
| Coverage result | `SC_05`, `1/3`, `33.3%`, `SH_12`, `SH_13`, `OPEN` |
| Follow-up action for Coverage | None |
| Schedule route | `ACTOR_DELAY` → `SCHEDULE_AGENT` |
| Schedule result | PENDING evidence-backed proposal |
| Schedule before approval | Unchanged |
| Autonomous schedule approval | Blocked |
| Optional human approval | APPROVED/reordered plus `HUMAN_DECISION` |
| Final reset | Active result cleared; unified workspace restored |
