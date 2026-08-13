# ADR-005 — Google ADK and Vertex AI Agent Runtime integration

**Status:** ACCEPTED FOR LOCAL REAL-AI MILESTONE
**Verification date:** 2026-08-13
**Milestone:** `STUDIOGRID_AI_REAL_AGENT_RUNTIME_2`

## Decision

StudioGrid AI uses Google's Agent Development Kit for its runtime agent graph and
Gemini inference through Vertex AI. Agents receive production state as data and
can call only typed functions that cross the FastAPI Tool Server boundary. The
Tool Server owns validation, authorization, human approval gates, state mutation,
Firestore persistence, and audit events.

No OpenAI, Anthropic, LangChain, CrewAI, AutoGen, or other third-party AI runtime
is part of the product.

## Official documentation verified

| Topic | Official source |
|---|---|
| Gemini 3.6 Flash model ID, GA status, function calling | https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash |
| Gemini 3.6 Flash Vertex/Agent Platform endpoint | https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-6-flash |
| Model endpoint locations | https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/locations |
| ADK Python agents and function tools | https://google.github.io/adk-docs/agents/llm-agents/ and https://google.github.io/adk-docs/tools/function-tools/ |
| ADK sessions | https://google.github.io/adk-docs/sessions/ |
| Agent Engine overview and supported regions | https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview |
| Develop ADK applications with `AdkApp` | https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/develop/adk |
| Deploy an Agent Engine application | https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/deploy |
| `AdkApp` Python reference | https://cloud.google.com/python/docs/reference/vertexai/latest/vertexai.agent_engines.AdkApp |
| Agent Engine sessions | https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview |
| Agent Engine tracing and logging | https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing |
| Application Default Credentials | https://cloud.google.com/docs/authentication/application-default-credentials |
| Firestore Python server client | https://cloud.google.com/firestore/docs/create-database-server-client-library |

## Verified packages and imports

The local environment and dependency files pin:

| Distribution | Version | Imports used |
|---|---:|---|
| `google-adk` | `2.6.3` | `google.adk.agents.LlmAgent`, `google.adk.agents.SequentialAgent`, `google.adk.runners.InMemoryRunner` |
| `google-cloud-aiplatform` | `1.164.0` | `vertexai.agent_engines.AdkApp` |
| `google-cloud-firestore` | `2.20.2` | `google.cloud.firestore.AsyncClient` |
| `google-genai` | `2.17.0` | ADK's Vertex Gemini transport and direct availability check |

Python 3.11 or newer is the repository requirement. The verification workstation
currently has Python 3.10.11 as well; Google client libraries warn that support for
Python 3.10 ends on 2026-10-04, so deployment images must use Python 3.11+.

## Model and locations

- Required and selected model: `gemini-3.6-flash`.
- Launch stage: GA (released 2026-07-21).
- Vertex model endpoint: `global` only, per the official model card.
- Project: `studiogrid-ai`.
- Managed Agent Engine location: `europe-west3` (Frankfurt), which is an officially
  supported Agent Engine region.
- Firestore database: `(default)`.
- Staging bucket reserved for a later deployment:
  `gs://studiogrid-ai-agent-staging`.

The model and Agent Engine therefore intentionally use different location settings:

```text
GOOGLE_CLOUD_LOCATION=global
GOOGLE_CLOUD_AGENT_ENGINE_LOCATION=europe-west3
```

On 2026-08-13, a live ADC-authenticated Vertex request in project `studiogrid-ai`
returned the exact sentinel `STUDIOGRID_MODEL_OK` from `gemini-3.6-flash` at
location `global`. No silent fallback model is permitted by runtime configuration.

## Local runtime

`PRODUCTION_ORCHESTRATOR` is a real ADK `SequentialAgent` containing the relevant
specialist for each typed event route:

```text
ACTOR_DELAYED
  -> PRODUCTION_ORCHESTRATOR (Google ADK)
  -> SCHEDULE_AGENT (LlmAgent, gemini-3.6-flash)
  -> create_schedule_proposal (the only exposed schedule function)
  -> HTTP FastAPI Tool Server
  -> Pydantic + ToolRegistry + authorization
  -> application state + Firestore + audit
  -> human-only approve endpoint
  -> schedule mutation + timeline audit
```

`SHOT_COMPLETED` follows the same graph through `COVERAGE_AGENT`, whose only
mutation function is `create_coverage_alert`.

Local ADK sessions use `InMemoryRunner`/`InMemorySessionService`. This is suitable
for the single-event local smoke. Managed deployment will let `AdkApp` use Agent
Engine's managed session service.

## Deployment mechanism (prepared, not executed)

`agents.google_adk.agent_graph.build_adk_app()` returns:

```python
from vertexai.agent_engines import AdkApp

AdkApp(
    agent=root_agent,
    app_name="studiogrid-ai",
    enable_tracing=True,
)
```

The deployment package must pin the same dependencies and upload through the
configured staging bucket. No deployment is performed by this milestone. Before
the first deployment, the user must confirm the exact runtime principal and grant
only the minimum roles described below.

## Authentication and IAM

Local authentication uses ADC from `gcloud auth application-default login` and
the quota project `studiogrid-ai`. No service-account key file is read or written.

Candidate least-privilege roles for the future runtime principal:

| Role | Reason |
|---|---|
| `roles/aiplatform.user` | Invoke Vertex Gemini and run the Agent Engine application |
| `roles/datastore.user` | Read and write the StudioGrid Firestore namespace |
| `roles/logging.logWriter` | Write structured operational logs |
| `roles/cloudtrace.agent` | Export traces when `enable_tracing=True` |
| scoped object access to `gs://studiogrid-ai-agent-staging` | Read deployment artifacts only if required by the chosen deployment path |

No Owner or Editor role is required.

## State and trust boundaries

- ADK agents do not import or instantiate Firestore clients.
- Function tool output is parsed again by Pydantic and checked against
  server-computed eligible scenes or factual missing shots.
- Agent tools are exposed under `/tools/agent/*`; no approve or reject function
  exists in the ADK allowlist or agent tool router.
- `approve_schedule_proposal` and `reject_schedule_proposal` remain HUMAN-only in
  `ToolRegistry` and `ApprovalGate`.
- Untrusted production notes are explicitly labeled data. Even a successful
  prompt injection cannot obtain a human-only tool.
- Gemini failure creates no fake proposal and leaves deterministic controls usable.
- `CONNECTED` is set only after a successful real ADK/Gemini execution and safe
  trace persistence.

## Firestore layout and cleanup

All demo documents are isolated beneath:

```text
productions/last-light-demo
  state/current
  proposals/{proposalId}
  coverage_alerts/{alertId}
  events/{eventId}
  agent_executions/{executionId}
```

Cleanup code is guarded to `productionId=last-light-demo`, is never automatic,
and never deletes a database or another collection.

## Safe execution trace

Stored fields are `executionId`, `correlationId`, `agentName`, `modelName`,
`eventId`, timestamps, `durationMs`, typed tool calls, `status`, `errorCode`,
`evidenceReferences`, and `shortRationale`. Private chain-of-thought is neither
requested nor stored.
