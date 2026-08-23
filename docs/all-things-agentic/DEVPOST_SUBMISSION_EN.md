# Devpost submission — English

## Title

StudioGrid AI

## Tagline

AI Production Control Room

## Category

The Taskmaster

## One-line pitch

StudioGrid turns a live film-production disruption into an evidence-backed schedule action through a real Google ADK multi-agent workflow, while reserving consequential approval for a human production manager.

## Problem

A film production day is a live constraint system. An actor is delayed. Exterior light is disappearing. Locations are available only during limited windows. Scenes are completed out of order, and required coverage may still be missing. One disruption can affect performers, camera, locations, art, continuity, and editorial at once.

Traditional production tools record the plan. The hard operational work begins when reality stops matching it.

## Solution

StudioGrid AI is a production control room that reasons over structured, changing production state. When an event arrives, its deployed Production Orchestrator routes the work to a specialist agent. The agent evaluates the actual actors, scenes, locations, dependencies, schedule order, daylight constraints, and completed shots; invokes a typed private tool; and persists an actionable result.

It is not a script generator or a chatbot. It performs a bounded operational workflow.

## Why this is agentic

The user reports an event, not a solution. For the Maya Reed delay, the user does not select an alternative scene, list affected dependencies, calculate a new order, or construct a recommendation. A real Vertex AI Agent Engine session runs a Google ADK application. The Production Orchestrator delegates to the Schedule Agent, Gemini 3.6 Flash reasons over verified production context, and the agent calls `create_schedule_proposal()` through an authenticated private Tool Server.

The result is a durable PENDING recommendation with why, evidence, expected benefit, risks, confidence, affected scenes, and a concrete reorder. That multi-step work is autonomous. A human is involved only where authority should change hands: applying or rejecting a consequential production mutation.

## Golden workflow

1. **FACT:** Maya Reed (`ACT_02`) is delayed by 45 minutes.
2. The private Control API creates the structured production event.
3. Vertex AI Agent Engine runs the deployed ADK Production Orchestrator.
4. The Orchestrator routes the event to the Schedule Agent.
5. Gemini 3.6 Flash evaluates actor-dependent scenes, eligible alternatives, locations, dependencies, schedule order, and daylight constraints.
6. The Schedule Agent invokes `create_schedule_proposal()` on the IAM-private Tool Server.
7. Firestore persists a PENDING recommendation and safe execution evidence.
8. The agent cannot approve or reject its own recommendation.
9. A production manager clicks APPROVE.
10. The Control API applies the proposed reorder and writes a `HUMAN_DECISION` event.
11. Refreshing the browser shows the same persisted proposal, schedule state, and timeline.

## What the agent does autonomously

- Receives a structured disruption event.
- Routes the event to the appropriate specialist.
- Builds context from current production state rather than free-form user instructions.
- Evaluates constraints and eligible work.
- Selects and invokes an allowlisted typed tool.
- Creates a proposal or coverage alert.
- Persists operational state and safe evidence metadata.
- Fails closed when a tool rejects an invalid mutation.

## Why human approval exists

Changing a shooting schedule affects an entire crew. StudioGrid treats that as an authority boundary, not another reasoning step. Agents may create PENDING proposals; they do not receive the human approve/reject tools. The server-side `ApprovalGate` rejects AGENT and SYSTEM callers even if model behavior is compromised.

The manager does not guide the agent's work. They authorize—or refuse—the already-completed recommendation. This preserves autonomous execution without giving a probabilistic system unilateral control over a high-impact operation.

## Multi-agent architecture

The public Next.js interface runs on Cloud Run. Its server-side BFF obtains a Google ID token to call an IAM-private Control API. The Control API invokes a deployed Vertex AI Agent Engine application. A Google ADK Production Orchestrator delegates to either the Schedule Agent or Coverage Agent. Gemini 3.6 Flash performs model reasoning; specialist agents call typed tools on a second IAM-private Cloud Run service. Firestore stores production state, proposals, alerts, events, demo sessions, and execution evidence.

The AI authority path and human decision path are deliberately separate.

## Schedule Agent

For an `ACTOR_DELAYED` event, the Schedule Agent receives factual structured context: the delayed actor, current schedule, actor-scene relationships, candidate scenes, location windows, dependencies, and daylight constraints. It can create only a PENDING proposal. ACT_02/Maya and ACT_03/Daniel exercise the same generic workflow with different actors and schedule effects.

## Coverage Agent

The Coverage Agent compares planned and completed shots for a real scene in the synthetic production state. In the golden demo it identifies `SH_12` and `SH_13` as missing, then creates an OPEN coverage alert through `create_coverage_alert()`. This is a second operational workflow, not text generated from a prompt.

## Google ADK

Google ADK 2.6.3 defines the deployed orchestration graph and specialist agents. The Production Orchestrator transfers work to the Schedule Agent or Coverage Agent, and the ADK application is packaged for Vertex AI Agent Engine.

## Gemini 3.6 Flash

StudioGrid uses `gemini-3.6-flash` through Vertex AI. The model reasons over server-built production context and selects typed tools. The application persists safe operational metadata—agent, model, execution ID, correlation ID, duration, tool name, status, and evidence references—rather than prompts or chain-of-thought.

## Vertex AI Agent Engine

The live ADK application is deployed as:

`projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`

The public demo invokes this remote resource for Schedule and Coverage flows. It is configured to scale from zero with a bounded maximum instance count.

## Cloud Run

Three services establish a deliberate public/private boundary:

- `studiogrid-web` — public judge-facing Next.js application.
- `studiogrid-control-api` — private control plane; only the web runtime identity invokes it.
- `studiogrid-tool-server` — private typed-tool surface; the Agent Engine runtime identity invokes it.

Unauthenticated requests to both private services are denied.

## Firestore

Firestore is the durable source for demo application state, proposals, coverage alerts, production events, execution evidence, and per-browser demo sessions. Approval changes schedule state, and refresh persistence demonstrates that the result is not a client-side animation.

## Cloud Trace

Agent Engine telemetry and correlation identifiers connect a user-visible action to cloud execution. Repository evidence includes a sampled Cloud Trace identifier while excluding messages, prompts, credentials, and chain-of-thought.

## Security

- Browser traffic reaches only the public web service.
- The BFF validates a fixed action schema, caps body size, rate-limits by demo session/IP, and uses a server-side identity token.
- The Control API accepts only fixed actor/delay combinations and rejects extra fields.
- Agents call an isolated, IAM-private Tool Server and never access Firestore directly.
- Typed Pydantic schemas validate tool inputs and state transitions.
- Agent-created schedule proposals must be PENDING and reference known scenes.
- Human approve/reject operations are enforced server-side.
- ADC and service identities are used; no service-account JSON keys are stored in the repository.

## Prompt-injection defense

The public demo never forwards arbitrary user prompts into the agent. Its API accepts a small allowlist of structured operations, and Pydantic models forbid additional fields such as `prompt`. More importantly, safety does not depend on the model obeying text instructions: even a compromised agent attempting `approve_schedule_proposal` or `reject_schedule_proposal` is rejected by the server-side approval gate. Tests exercise both cases.

## Failure handling

Tool authorization and schema checks fail closed. A recorded Agent Engine failure probe attempted an invalid scene mutation, produced `ToolServerError`, persisted an ERROR execution trace, and created zero new proposals. Firestore startup failure disables the AI runtime rather than silently switching to an unverified cloud state.

## FACT / INFERENCE / RECOMMENDATION / HUMAN_DECISION

StudioGrid keeps four categories distinct in data and UI:

- **FACT:** Maya Reed is delayed by 45 minutes.
- **INFERENCE:** actor-dependent scenes are temporarily blocked and eligible alternatives exist.
- **RECOMMENDATION:** reorder specific production work.
- **HUMAN_DECISION:** approve or reject the persisted recommendation.

This prevents model output from being presented as an observed fact and preserves a reviewable production timeline.

## Public demo

<https://studiogrid-web-729921508335.europe-west3.run.app>

Recommended path: Reset Demo → Maya Reed 45m → wait for PENDING proposal → inspect evidence → approve → compare before/after → inspect `HUMAN_DECISION` → run Coverage Check.

## Technologies used

- Gemini 3.6 Flash via Vertex AI
- Google ADK 2.6.3
- Vertex AI Agent Engine
- Cloud Run
- Firestore
- Cloud Trace / Google Cloud telemetry
- Python 3.12, FastAPI, Pydantic
- Node.js 22, Next.js 16, React 19, TypeScript

## Data sources

StudioGrid uses the original, fictional **LAST LIGHT** production package stored in `demo/last_light/production_package.json`. It contains synthetic actors, locations, scenes, shots, dependencies, continuity facts, and a shooting schedule. The demo uses no real customer or film-studio data.

## Findings and learnings

The most important design lesson was that autonomy and authority are different. An agent can perform extensive operational work while a deterministic service controls the final high-impact mutation. Separating those concerns made the system easier to test, audit, and explain.

We also learned that a convincing agent demo needs durable evidence. A polished answer is not enough: the proposal, tool result, state change, and human decision must survive refresh and remain traceable to the remote execution.

## Challenges

- Packaging a real ADK multi-agent application for Agent Engine while keeping its Tool Server private.
- Preserving service-to-service identity across public web, private control, managed agent runtime, and private tools.
- Making a deterministic reset coexist with durable Firestore evidence.
- Exposing enough technical proof for judges without exposing prompts, credentials, or chain-of-thought.
- Keeping the approval gate outside the model's authority without turning the workflow into manual step-by-step guidance.

## What's next

Future work would add opt-in production integrations, richer constraint solvers, resumable event ingestion, role-specific notifications, and expanded observability. Those are roadmap items, not claims about the current demo. The current submission is intentionally scoped to a verified synthetic production package and two complete operational workflows.

## Technical evidence

- `docs/evidence/agent-engine-cloud-3b.json`
- `docs/evidence/cloud-demo-3c/deployment.json`
- `docs/evidence/cloud-demo-3c/browser-verification.md`
- `docs/all-things-agentic/architecture.mmd`
- `docs/all-things-agentic/assets/studiogrid-architecture.png`
- `tests/unit/test_agent_engine_cloud.py`
- `tests/unit/test_phase2_agents.py`
- `tests/unit/test_approval_gates.py`
- `tests/unit/test_tool_authorization.py`
