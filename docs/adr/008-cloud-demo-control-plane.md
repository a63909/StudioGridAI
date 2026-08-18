# ADR 008: Public cloud demo control plane

- Status: Accepted
- Date: 2026-08-18
- Milestone: `STUDIOGRID_AI_CLOUD_DEMO_CONTROL_PLANE_3C`

## Context

StudioGrid already has a deployed Vertex AI Agent Engine production orchestrator, a private Cloud Run Tool Server, and a Firestore-backed synthetic `LAST LIGHT` demo. The hackathon demo needs a public browser entry point without making either privileged human mutations or the existing Tool Server public.

The browser must never receive a Google access token, Google-signed ID token, service-account key, ADC credential, privileged Firestore credential, selectable model, selectable Agent Engine resource, or arbitrary tool/path input.

## Decision

Use two new Cloud Run trust boundaries in `europe-west3`:

```text
public browser
  -> public studiogrid-web (Next.js UI and same-origin BFF)
  -> private studiogrid-control-api (FastAPI)
  -> existing Vertex AI Agent Engine / Firestore
  -> existing private studiogrid-tool-server (only from Agent Engine)
```

`studiogrid-web` is the only unauthenticated service. Its Node.js route handlers validate a closed operation union, enforce a small request body limit and in-memory rate limit, issue an opaque `demoSessionId` cookie, and call only the configured Control API. Server-side Application Default Credentials mint a Google-signed ID token whose audience is the Control API's canonical Cloud Run URL.

`studiogrid-control-api` remains IAM-authenticated Cloud Run. It exposes only health and closed demo operations. It invokes the fixed Agent Engine resource `projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`, reconciles the resulting PENDING proposal or coverage alert from Firestore, and applies approval/rejection only with `OriginType.HUMAN` through the existing approval gate. It never accepts an arbitrary resource, model, tool name, production ID, Firestore path, actor ID, or scene ID.

The existing `studiogrid-tool-server` remains private and its public-access policy is unchanged.

## Identities and IAM

- `studiogrid-web-runtime@studiogrid-ai.iam.gserviceaccount.com`: no project roles. It receives resource-level `roles/run.invoker` only on `studiogrid-control-api`.
- `studiogrid-control-runtime@studiogrid-ai.iam.gserviceaccount.com`: project roles `roles/aiplatform.user` (query the existing Agent Engine), `roles/datastore.user` (read/write application data), and `roles/logging.logWriter` (write runtime logs).

No Owner, Editor, Service Account Token Creator, Storage Admin, project-wide Cloud Run Invoker, service-account key, `allAuthenticatedUsers`, or Control API `allUsers` binding is part of this design. Any additional role is an `IAM_BLOCKER` pending explicit review.

## Demo state and evidence preservation

The only permitted production namespace is `productions/last-light-demo`. Each browser receives a validated opaque session identifier used in Agent Engine user IDs and correlation IDs. A session document records its active proposal/alert and before/after schedule snapshots.

`RESET DEMO` loads the checked-in `LAST LIGHT` package and overwrites only `productions/last-light-demo/state/current`, then starts a new session epoch. It does not delete Firestore documents, historical proposals, executions, events, Cloud Run services, or Agent Engine resources. Historical evidence remains available; session-scoped responses never surface another browser's active proposal as the current one.

Both services use `min-instances=0`, `max-instances=1`, and request-based billing. The single Control API instance avoids concurrent writes to the canonical synthetic schedule; application locks serialize state-changing operations. Rate limiting is a practical demo safeguard, not an identity boundary.

## Runtime truth and failure behavior

`CONNECTED` is derived from real Firestore access and successful remote Agent Engine evidence. Agent Engine, Gemini, and private Tool Server become connected only after a remote session returns a successful durable execution/tool result; static environment configuration is insufficient. Failures return safe error codes, preserve PENDING proposals, and never synthesize a proposal, alert, approval, or schedule change.

The technical evidence response contains only safe operational metadata: agent/model names, execution/session/correlation IDs, durations, evidence references, and persistence/tool status. Prompts, tokens, credentials, raw session context, and chain-of-thought are excluded.

## Deployment choices verified against current Google documentation

- Next.js on Cloud Run supports source deployment and container deployment: <https://docs.cloud.google.com/run/docs/quickstarts/frameworks/deploy-nextjs-service>
- Cloud Run service-to-service authentication uses a Google-signed ID token and the receiving service URL as `aud`: <https://docs.cloud.google.com/run/docs/authenticating/service-to-service>
- User-managed per-service runtime identities and least privilege: <https://docs.cloud.google.com/run/docs/configuring/services/service-identity>
- Resource-level Cloud Run Invoker is the receiving-service authorization boundary: <https://docs.cloud.google.com/run/docs/securing/managing-access>
- Cloud Run minimum and maximum instance controls: <https://docs.cloud.google.com/run/docs/configuring/min-instances> and <https://docs.cloud.google.com/run/docs/configuring/max-instances>
- Agent Engine setup and `roles/aiplatform.user`: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/set-up>
- Agent Engine sessions API: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/manage-sessions-api>
- Firestore application read/write role `roles/datastore.user`: <https://docs.cloud.google.com/firestore/docs/security/iam>
- Cloud Logging writer role `roles/logging.logWriter`: <https://docs.cloud.google.com/logging/docs/access-control>

## Consequences

The public site needs no localhost service and cannot directly mutate Firestore or call Google Cloud APIs. The Control API and Tool Server remain private IAM-protected resources. Canonical demo state is intentionally shared and serialized because the already-deployed Agent Engine Tool Server writes the fixed `last-light-demo` namespace; session correlation and deterministic non-destructive reset provide practical judge isolation while retaining auditable evidence.
