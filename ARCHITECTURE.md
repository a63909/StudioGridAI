# StudioGrid AI — architecture

## Current verified deployment

StudioGrid is an event-driven, multi-agent production control system for the synthetic LAST LIGHT shoot. It separates the public browser, private control plane, managed agent runtime, private typed tools, durable state, and human authority.

The submission diagram is maintained as:

- Source: [docs/all-things-agentic/architecture.mmd](docs/all-things-agentic/architecture.mmd)
- Render: [docs/all-things-agentic/assets/studiogrid-architecture.png](docs/all-things-agentic/assets/studiogrid-architecture.png)

```text
PUBLIC BROWSER
  → PUBLIC CLOUD RUN: studiogrid-web
  → server-side authenticated Next.js BFF
  → PRIVATE CLOUD RUN: studiogrid-control-api
  → VERTEX AI AGENT ENGINE
  → GOOGLE ADK PRODUCTION_ORCHESTRATOR
      ├─ SCHEDULE_AGENT
      └─ COVERAGE_AGENT
  ↔ GEMINI 3.6 FLASH
  → authenticated typed tools
  → PRIVATE CLOUD RUN: studiogrid-tool-server
  → FIRESTORE

PENDING proposal
  → HUMAN APPROVE / REJECT (outside AI authority)
  → Control API
  → schedule mutation or rejection + HUMAN_DECISION
  → Firestore
```

## Deployed resources

| Component | Resource/purpose |
|---|---|
| Public web | Cloud Run `studiogrid-web`; judge-facing Next.js UI and server-side BFF |
| Private control | Cloud Run `studiogrid-control-api`; fixed demo operations and human decision boundary |
| Managed agent runtime | `projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024` |
| Agent framework | Google ADK 2.6.3 |
| Model | `gemini-3.6-flash` through Vertex AI |
| Private tools | Cloud Run `studiogrid-tool-server`; typed create operations for agents |
| Durable state | Firestore application state, proposals, alerts, events, sessions, and safe execution evidence |
| Telemetry | Cloud Trace plus execution/correlation metadata |

## Agent graph

| Agent | Input | Allowed operational output |
|---|---|---|
| `PRODUCTION_ORCHESTRATOR` | Structured event plus server-built context | Transfer to Schedule or Coverage specialist |
| `SCHEDULE_AGENT` | Actor delay, schedule, actor/scene relationships, eligible scenes, locations, dependencies, daylight | PENDING schedule proposal via `create_schedule_proposal` |
| `COVERAGE_AGENT` | Planned/completed shot facts for a scene | OPEN coverage alert via `create_coverage_alert` |

Agents do not receive general database access and do not receive the human approval tools.

## State and event model

State changes are represented with typed Pydantic objects. Operational evidence separates:

- **FACT** — recorded production input;
- **INFERENCE** — derived consequence;
- **RECOMMENDATION** — proposed action;
- **HUMAN_DECISION** — explicit approval or rejection.

Firestore persists the public demo's application state and audit evidence. The UI reloads state through the private control path; approved state surviving refresh is a durability assertion.

## Mutation path

```text
Agent
  → typed tool call
  → IAM-private Tool Server
  → caller authorization
  → Pydantic/schema/state validation
  → PENDING proposal or OPEN alert
  → Firestore + safe execution trace

Human
  → fixed APPROVE/REJECT action
  → authenticated BFF
  → private Control API
  → server-side ApprovalGate
  → state mutation + HUMAN_DECISION
  → Firestore
```

## Security boundaries

1. Only the web service is public.
2. The web runtime identity may invoke only the private Control API.
3. The Agent Engine runtime identity invokes the private Tool Server.
4. Agents never access Firestore directly.
5. Request schemas forbid arbitrary prompt fields in the public demo.
6. Agent-created schedule proposals must be PENDING and reference known scenes.
7. `ApprovalGate` rejects AGENT/SYSTEM approve and reject calls.
8. Evidence includes safe operational metadata, not credentials, raw prompts, or chain-of-thought.

## Failure behavior

- Invalid tool mutations fail closed.
- Tool failures produce safe error codes and ERROR execution evidence.
- The verified invalid-scene probe created no new proposal.
- Firestore initialization failure disables the real-agent path rather than continuing with an unverified durable state.
- Agent Engine and Cloud Run scale from zero; cold-start latency is expected and does not grant a fallback authority path.

## Historical Phase 1 components

The repository also contains deterministic Continuity, Risk, and Wrap agents from Phase 1. They remain useful domain/test artifacts but are not represented as deployed Vertex AI Agent Engine specialists in the public golden flow. The verified cloud claim is limited to Production Orchestrator, Schedule Agent, and Coverage Agent.

## ADR index

- [ADR 001 — Event-driven state](docs/adr/001-event-driven-state.md)
- [ADR 002 — Agent interfaces](docs/adr/002-agent-interfaces.md)
- [ADR 003 — Human approval gates](docs/adr/003-human-approval-gates.md)
- [ADR 005 — Google agent runtime integration](docs/adr/005-google-agent-runtime-integration.md)
- [ADR 006 — Private Cloud Run Tool Server](docs/adr/006-private-cloud-run-tool-server.md)
- [ADR 007 — Vertex Agent Engine cloud runtime](docs/adr/007-vertex-agent-engine-cloud-runtime.md)
- [ADR 008 — Cloud demo control plane](docs/adr/008-cloud-demo-control-plane.md)
