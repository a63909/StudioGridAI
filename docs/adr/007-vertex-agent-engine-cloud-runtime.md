# ADR 007: Vertex AI Agent Engine cloud runtime for StudioGrid agents

- Status: Accepted
- Date: 2026-08-13
- Milestone: `STUDIOGRID_AI_AGENT_ENGINE_CLOUD_3B`

## Context

StudioGrid already has real Google ADK Schedule and Coverage agents, typed
Pydantic tool contracts, a private Cloud Run Tool Server, Firestore persistence,
and human-only schedule approval gates. The missing production boundary was a
managed remote agent runtime: the existing real agents created an ADK
`InMemoryRunner` inside the API process.

The cloud runtime must execute real Gemini inference, use the existing private
tool boundary, preserve human approval, use a least-privilege custom runtime
identity, retain safe operational traces, and support durable remote sessions.
It must not expose a browser-facing Agent Engine endpoint or deploy the frontend.

## Decision

Deploy one `AdkApp` to Vertex AI Agent Engine (also documented as Agent Platform
Runtime) using the current `agentplatform.Client.agent_engines.create` API from
`google-cloud-aiplatform[agent-engines,adk]` 1.164.0.
The SDK `extra_packages` entries are repository-root-relative (`agents` and
`services`) so their top-level Python package names are preserved in the runtime
archive.

The deployed graph is:

```text
PRODUCTION_ORCHESTRATOR (gemini-3.6-flash)
  -> SCHEDULE_AGENT (ACTOR_DELAYED)
       -> create_schedule_proposal
  -> COVERAGE_AGENT (SHOT_COMPLETED)
       -> create_coverage_alert
```

The Production Orchestrator is an ADK `LlmAgent` with both specialists as
sub-agents. It routes typed events and has no production mutation tool of its
own. The specialist prompts are shared with the existing real local agents.

Each remote invocation creates an Agent Engine session with JSON-safe initial
state containing:

- immutable event identity and correlation ID;
- a unique agent execution ID and start time;
- factual schedule eligibility or factual coverage sets computed from the LAST
  LIGHT production state;
- one-attempt and mutation-result guards.

The user message contains the same factual context, explicitly classified as
untrusted data. The function tool validates its arguments again against session
state before making an external request. Agent Engine session state records only
operational results such as proposal/alert IDs, statuses, and error codes.

## Runtime and model locations

- Agent Engine resource: `europe-west3` (Frankfurt).
- Gemini model: `gemini-3.6-flash` through the `global` model endpoint.
- Staging bucket: `gs://studiogrid-ai-agent-staging` in `EUROPE-WEST3`.
- Python runtime: 3.12.

Agent Engine and Gemini locations are intentionally separate configuration
values. The deployed ADK `Gemini` object explicitly supplies project and
`location="global"` in `client_kwargs`; it does not override Agent Engine's
platform-managed region environment. No regional model substitution is allowed.

## Identity and private tools

The deployment specifies only the email of the existing custom runtime service
account:

`studiogrid-agent-runtime@studiogrid-ai.iam.gserviceaccount.com`

The runtime service account already has Vertex AI User, log writer, trace agent,
and service-level Cloud Run Invoker on `studiogrid-tool-server`. Deployment does
not grant or widen IAM roles.

The only mutation path available to the remote agents is the existing canonical
private service URL:

`https://studiogrid-tool-server-udlec7cupa-ey.a.run.app`

`FastAPIToolGateway` obtains a short-lived Google-signed ID token from runtime
ADC, uses the canonical service URL as `aud`, and sends it in the Authorization
header. Tokens are never stored or logged. The Tool Server exposes only agent
create-proposal, create-coverage-alert, and safe-trace routes; approve and reject
routes remain absent from the agent router.

## Sessions, traces, and failure safety

Remote smoke tests use `async_create_session(state=...)`,
`async_stream_query(...)`, `async_get_session(...)`, and
`async_list_sessions(...)`. They retain the resource name, session IDs, safe
function-call summaries, Firestore IDs, statuses, and correlations as evidence.

`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` enables Agent Engine
OpenTelemetry traces and logs. We deliberately do **not** set
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, so prompts and responses
are not captured by telemetry. StudioGrid also persists its established safe
`AgentExecution` record with model name, timestamps, duration, tool status,
correlation, evidence references, and concise rationale—never chain-of-thought.

A failed private tool call sets the session error code and persists an ERROR
trace when the trace endpoint is reachable. It never persists a SUCCESS trace.
The one-attempt guard is set before the HTTP mutation attempt, which prevents an
LLM retry from producing a duplicate mutation after an ambiguous failure.

## Human approval invariant

Schedule agents may create only `PENDING` proposals. They cannot approve or
reject them, and a proposal does not reorder the schedule. The existing
human-only approval route and `ApprovalGate` remain the only path that applies a
schedule change.

## Consequences

- Gemini reasoning and ADK orchestration now run in the managed remote runtime.
- Cloud Run remains the single authenticated authorization and mutation
  boundary; Firestore remains its durable mirror.
- A caller must compute or retrieve trusted production context before creating a
  remote session. A future public API must therefore create sessions server-side
  rather than accept arbitrary session state from browsers.
- Managed runtime scale-to-zero can add cold-start latency; the deployment uses
  min instances 0 and max instances 1 for this milestone.
- The Agent Engine resource and its evidence are retained; no automatic cleanup
  or deletion is performed.

## Verified deployment

- Resource: `projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`
- Effective identity: `studiogrid-agent-runtime@studiogrid-ai.iam.gserviceaccount.com`
- Tool Server revision: `studiogrid-tool-server-00002-bpz`
- Safe smoke evidence: `docs/evidence/agent-engine-cloud-3b.json`

## Official references reviewed

- [Deploy an agent and configure a custom service account](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/deploy)
- [Develop an ADK agent for Agent Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/develop/adk)
- [Agent Engine overview and supported regions](https://cloud.google.com/vertex-ai/generative-ai/docs/reasoning-engine/overview)
- [AdkApp session and async query API](https://docs.cloud.google.com/python/docs/reference/vertexai/latest/vertexai.agent_engines.AdkApp)
- [Trace an Agent Engine agent](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing)
- [Authenticate Cloud Run service-to-service requests](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
