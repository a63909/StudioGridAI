# Manual Google Cloud console capture instructions

Use these steps only for the two console images that browser automation could not save. Do not change APIs, IAM, resources, or data.

## 10-cloud-agent-engine.png

1. Open Google Cloud Console for project `studiogrid-ai`.
2. Navigate to **Agent Platform → Deployments**.
3. Confirm the table row shows:
   - `studiogrid-production-orchestrator-3b`;
   - resource suffix `5132986471388545024`;
   - framework `google-adk`;
   - region `europe-west3 (Frankfurt)`;
   - telemetry enabled.
4. Either capture the sanitized deployment row or open the resource detail Dashboard.
5. Crop out the account avatar/email, other projects, billing/credit banners, and unrelated resources.
6. Do not enable `apphub.googleapis.com` if the detail page offers it; that API is not required for the evidence capture.
7. Save exactly as `docs/all-things-agentic/evidence/10-cloud-agent-engine.png`.

## 12-firestore.png

1. Open **Firestore Studio** for project `studiogrid-ai`, database `(default)`.
2. Select `productions` → `last-light-demo`.
3. Keep these synthetic subcollections visible:
   - `agent_executions`
   - `coverage_alerts`
   - `demo_sessions`
   - `events`
   - `proposals`
   - `state`
4. Keep `productionId = last-light-demo` and `sourceProductionId = PROD_LAST_LIGHT_001` visible if they fit.
5. Do not open a credential, token, raw prompt, or unrelated document.
6. Crop out account email/avatar, billing information, and unrelated projects.
7. Save exactly as `docs/all-things-agentic/evidence/12-firestore.png`.

## Review before commit/publication

- Zoom to 100% and inspect every visible string.
- Confirm there is no personal email or browser-profile detail.
- Confirm no raw model message or chain-of-thought appears.
- Confirm all records are under the synthetic `last-light-demo` namespace.
- Update `evidence/EVIDENCE_INDEX.md` only after the real image exists.
