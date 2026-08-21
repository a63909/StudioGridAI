# All Things Agentic screenshot evidence index

Captured from the real deployed product and Google Cloud on **2026-08-21**. No UI screenshot is fabricated. Images exclude credentials, tokens, raw prompts, chain-of-thought, customer data, and personal email text.

Public URL: <https://studiogrid-web-729921508335.europe-west3.run.app>

## Captured files

| File | Real state shown | Verification |
|---|---|---|
| [`01-dashboard.png`](01-dashboard.png) | Clean RESET dashboard, LAST LIGHT, public cloud UI | Public URL; synthetic baseline; 3 completed shots |
| [`02-maya-delay.png`](02-maya-delay.png) | ACT_02 factual actor-delay state | Maya Reed, 45 minutes |
| [`03-agent-running.png`](03-agent-running.png) | Live request in progress | “Agent Engine is running…”; captured immediately after one real click |
| [`04-pending-proposal.png`](04-pending-proposal.png) | Real PENDING Schedule Agent recommendation | Proposal `75e05d6a-4258-4c53-9b03-1814e4cfaa17` |
| [`05-evidence.png`](05-evidence.png) | Expanded safe technical evidence | execution `2f1f8ab8-4f56-4d86-86c3-d32d07b5e26d`; Gemini 3.6 Flash; `create_schedule_proposal`; 59,771 ms |
| [`06-human-approve.png`](06-human-approve.png) | Human-approved proposal | `APPROVED_BY_HUMAN`; AI authority remains separate |
| [`07-before-after.png`](07-before-after.png) | Durable schedule mutation | `SC_02` moved 2 → 1; before/after state |
| [`08-human-decision.png`](08-human-decision.png) | Post-refresh audit state | Approved state and `SCHEDULE_PROPOSAL_APPROVED` survived reload |
| [`09-coverage.png`](09-coverage.png) | Real Coverage Agent result | 1/3 completed; missing `SH_12`, `SH_13`; alert `10e0d9f2-ee00-4794-879e-38d62daf42fe` |
| [`11-cloud-run.png`](11-cloud-run.png) | Sanitized Cloud Run services table | Control API/Tool Server: Require authentication; Web: Public access |
| [`13-mobile.png`](13-mobile.png) | Public mobile layout | 390×844 override; `scrollWidth == clientWidth` (375 CSS px after scrollbar allocation) |
| [`14-russian.png`](14-russian.png) | Public Russian UI | RU labels, approved state, Coverage result, timeline |

## Not fabricated: capture gaps

Two requested console screenshots were not produced:

- `10-cloud-agent-engine.png`
- `12-firestore.png`

The signed-in console views were read successfully and verified live, but the in-app browser screenshot operation returned `Unable to capture screenshot` repeatedly on those two console surfaces. The project therefore keeps the slots absent rather than generating or relabeling an image.

Live assertions observed:

- Agent Engine console: `studiogrid-production-orchestrator-3b`; resource `projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`; framework `google-adk`; region `europe-west3 (Frankfurt)`; telemetry enabled; created August 13, 2026.
- Firestore Studio: `productions/last-light-demo` with subcollections `agent_executions`, `coverage_alerts`, `demo_sessions`, `events`, `proposals`, and `state`; `sourceProductionId = PROD_LAST_LIGHT_001`; live `updatedAt` on August 21, 2026.

Exact manual capture instructions are in [`../CLOUD_CONSOLE_CAPTURE_INSTRUCTIONS.md`](../CLOUD_CONSOLE_CAPTURE_INSTRUCTIONS.md).

## Capture integrity

- ACT_02 was recorded in one browser session from reset through remote execution, approval, reload, and Coverage.
- The remote call was not accelerated; cold execution lasted 59,771 ms.
- The final browser action reset only the synthetic demo state.
- Cloud Run screenshot was cropped before saving so account/profile and “deployed by” email data are not present.
