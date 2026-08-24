# Devpost submission — English

## Title

StudioGrid AI

## Tagline

AI Production Control Room

## Category

The Taskmaster

## One-line pitch

StudioGrid turns one natural-language production goal into a validated, evidence-backed operational workflow with Gemini, Google ADK, and Vertex AI Agent Engine—autonomously where the agent has authority, with deterministic human approval only when a consequential schedule mutation crosses the authority boundary.

## Problem

A film production day is not a static schedule. It is a live constraint system.

Production managers constantly react to actor delays, incomplete shot coverage, scene dependencies, location windows, daylight constraints, work completed out of order, and work that is temporarily blocked. One change can affect performers, camera, locations, art, continuity, editorial, and the rest of the crew at once.

Traditional production tools record the plan. They do not execute the operational reasoning required when reality stops matching it.

## Solution

**Give StudioGrid the production problem, not the steps.**

The operator writes one bounded production goal in the shared StudioGrid workspace:

> Check SC_05 and make sure all required coverage is complete.

StudioGrid safely classifies that untrusted language, validates a narrow typed intent, runs the deployed Google ADK specialist workflow on Vertex AI Agent Engine, inspects current production state, calls an authenticated private tool, and persists the operational result.

It is not an unrestricted chat-to-tools interface. The public contest build intentionally supports a small verified command surface: exact predefined actor-delay demo facts and the fixed `SC_05` shot-coverage check. Unsupported location, weather, equipment, arbitrary actor/delay, free-form mutation, and approval-bypass commands fail closed.

## Why this is agentic

StudioGrid has two deliberately separated reasoning layers.

### Layer 1 — safe command routing

Gemini 3.6 Flash receives the natural-language command as untrusted data. This classifier has **no tools, no mutation authority, and no path to the Tool Server**. It can return only:

- `ACTOR_DELAY` for an exact allowlisted synthetic actor/delay fact;
- `CHECK_COVERAGE` for the fixed shot-coverage workflow; or
- `UNSUPPORTED`.

Strict Pydantic validation rejects extra fields, invalid actor/delay pairs, and model output outside the allowlist. The raw command stops at this boundary and is never forwarded to the tool-enabled specialist.

### Layer 2 — operational agent execution

The private Control API turns the validated route into a typed operation. Vertex AI Agent Engine runs the deployed Google ADK Production Orchestrator, which delegates to the Schedule Agent or Coverage Agent. The specialist receives server-built factual production context—not the raw user command—reasons over that context with Gemini 3.6 Flash, and invokes only typed authenticated tools on the IAM-private Tool Server.

The result is durable operational state in Firestore, not just generated text.

## Taskmaster proof — one-command Coverage workflow

The primary golden workflow is:

> Check SC_05 and make sure all required coverage is complete.

After that single command, StudioGrid autonomously:

1. classifies the goal as `CHECK_COVERAGE`;
2. validates the typed route;
3. runs the Coverage Agent through the deployed ADK application;
4. compares actual planned and completed shot state for `SC_05`;
5. establishes that 1 of 3 required shots is complete (`33.3%`);
6. identifies missing shots `SH_12` and `SH_13`;
7. calls `create_coverage_alert` through the private Tool Server;
8. persists an `OPEN` alert and safe execution evidence in Firestore; and
9. returns the contextual result and execution ID to the same workspace.

**No additional user step is required after the command.** This is the clearest Taskmaster proof: one natural-language goal → autonomous routing → specialist reasoning → typed tool call → durable operational result.

## Schedule workflow — autonomy with bounded authority

The second proof begins with:

> Maya Reed is 45 minutes late. Keep today's shoot on schedule.

Gemini routes the exact supported fact to `ACTOR_DELAY`. The Schedule Agent receives current actor, scene, location, dependency, completed-work, schedule-order, and daylight facts. It evaluates constraints and calls `create_schedule_proposal` to persist a **PENDING** recommendation with:

- the proposed order;
- factual evidence;
- affected scenes;
- expected benefit;
- risks; and
- confidence.

The current schedule remains unchanged until a human production manager approves or rejects the proposal.

**Human approval is not manual orchestration.** The human does not select a replacement scene, enumerate constraints, route agents, or tell the system how to solve the problem. The autonomous workflow is already complete. Approval transfers authority only for the consequential real-world mutation.

**Autonomy where the agent has authority; deterministic human approval where a high-impact mutation crosses an authority boundary.**

## Why Schedule approval does not weaken the Taskmaster story

Coverage demonstrates fully autonomous end-to-end execution with no follow-up action. Schedule demonstrates a different production principle: autonomy is not the same as authority.

Agent routing, constraint analysis, proposal construction, tool execution, evidence creation, and persistence all complete before a human appears. A schedule mutation affects an entire crew, so StudioGrid deliberately keeps that final authority outside the model. The server-side `ApprovalGate` permits only a HUMAN caller to approve or reject the already-defined proposal.

## Multi-agent architecture

1. A public browser reaches `studiogrid-web` on Cloud Run.
2. Its authenticated server-side BFF obtains a Google ID token for the IAM-private Control API.
3. A tool-less Gemini 3.6 Flash Command Router maps untrusted language to a strict typed intent.
4. Pydantic validates the allowlist before any specialist workflow runs.
5. The Control API invokes the deployed Vertex AI Agent Engine application.
6. The Google ADK Production Orchestrator delegates the typed operation to Schedule or Coverage.
7. The specialist uses Gemini 3.6 Flash over server-built production context.
8. Typed authenticated tools call the IAM-private Tool Server.
9. Firestore stores production state, proposals, alerts, events, demo sessions, and safe execution evidence.
10. HUMAN APPROVE / REJECT remains a separate path through the Control API for consequential schedule changes.

## Schedule Agent

The Schedule Agent handles the exact allowlisted `ACTOR_DELAYED` demo facts: Maya Reed / `ACT_02` at 45 minutes and Daniel Osei / `ACT_03` at 30 minutes. It evaluates current production constraints and may create only a PENDING proposal. It has no approval tool.

## Coverage Agent

The Coverage Agent compares planned and completed shots for the fixed public `SC_05` workflow. It identifies `SH_12` and `SH_13` as missing and persists an OPEN alert via `create_coverage_alert`. The user does not need to press a second workflow button.

## Google ADK

Google ADK 2.6.3 defines the deployed Production Orchestrator and Schedule/Coverage specialists. The application is packaged for and executed on Vertex AI Agent Engine.

## Gemini 3.6 Flash

StudioGrid uses `gemini-3.6-flash` through Vertex AI in two bounded roles:

- a tool-less, zero-mutation command classifier; and
- specialist reasoning over server-built typed production context.

The application stores safe operational metadata—agent, model, execution ID, correlation ID, duration, typed tool name, status, and evidence references—rather than raw commands, credentials, or chain-of-thought.

## Vertex AI Agent Engine

The live ADK application is deployed as:

`projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024`

The public demo invokes this remote resource for the Schedule and Coverage workflows.

## Cloud Run

- `studiogrid-web` — public judge-facing Next.js application and authenticated BFF.
- `studiogrid-control-api` — IAM-private control plane, invoked by the web runtime identity.
- `studiogrid-tool-server` — IAM-private typed-tool surface, invoked by the Agent Engine runtime identity.

Unauthenticated requests to the private services are denied.

## Firestore

Firestore is the durable source for synthetic demo state, proposals, coverage alerts, production events, execution evidence, and per-browser demo sessions. Coverage alerts and schedule recommendations survive the request boundary; approved/rejected schedule decisions survive refresh.

## Cloud Trace

Execution and correlation identifiers connect a visible action to managed cloud telemetry. The evidence surface intentionally excludes messages, raw commands, credentials, and chain-of-thought.

## Security and prompt-injection defense

- The public UI accepts natural-language production commands, but limits their length and rate.
- Raw language enters only the isolated tool-less Gemini Command Router.
- The router has no tools, no mutation capability, and cannot call the Tool Server.
- Its output is validated against strict Pydantic/typed allowlists.
- Only a validated typed operation enters the existing agent workflow.
- Specialist agents receive server-built production context, never the raw command.
- Unsupported commands return `UNSUPPORTED` and never reach a specialist.
- Agents use typed tools on an IAM-private service and never access Firestore directly.
- Agent-created schedule proposals must be PENDING and reference known scenes.
- The server-side `ApprovalGate` rejects AGENT and SYSTEM approval/rejection callers even if a model were compromised.
- ADC and service identities are used; no service-account JSON keys are stored in the repository.

## Failure handling

Routing, schemas, authorization, and tools fail closed. Invalid classifier output, unsupported commands, invalid actor/delay pairs, or invalid tool mutations do not silently broaden the workflow. A recorded invalid-scene probe produced `ToolServerError`, persisted an ERROR execution trace, and created zero new proposals. Firestore startup failure disables the AI runtime instead of switching to an unverified state.

## FACT / INFERENCE / RECOMMENDATION / HUMAN_DECISION

- **FACT:** an observed production state, such as Maya Reed being delayed 45 minutes or only `SH_11` being complete for `SC_05`.
- **INFERENCE:** actor-dependent scenes are blocked, or required shots remain missing.
- **RECOMMENDATION:** a specific proposed schedule reorder.
- **HUMAN_DECISION:** approve or reject the persisted schedule proposal.

Keeping these categories separate prevents model conclusions from being presented as observed facts.

## Public demo

<https://studiogrid-web-729921508335.europe-west3.run.app>

Recommended path:

1. Reset Demo if needed.
2. Enter `Check SC_05 and make sure all required coverage is complete.`
3. Inspect `SC_05`, `1/3`, `33.3%`, `SH_12`, `SH_13`, `OPEN`, runtime status, and Technical details.
4. Reset and enter `Maya Reed is 45 minutes late. Keep today's shoot on schedule.`
5. Inspect the PENDING recommendation and unchanged schedule.
6. Optionally approve/reject to demonstrate the human authority boundary and durable audit.

Public repository: <https://github.com/a63909/StudioGridAI>

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

StudioGrid uses the original fictional **LAST LIGHT** package in `demo/last_light/production_package.json`. It contains synthetic actors, locations, scenes, shots, dependencies, continuity facts, and a shooting schedule. No real customer or film-studio data is used.

## Findings and learnings

The strongest agent boundary is not simply “human or no human.” It is the boundary between work the system can safely complete and authority it should not hold. Coverage can finish end-to-end. Schedule reasoning and proposal creation can also finish end-to-end, while the high-impact mutation remains deterministic and human-authorized.

We also learned that durable proof matters more than fluent output. A judge should be able to connect the visible result to a real Agent Engine execution, typed tool call, persisted state, and audit record.

## Challenges

- Safely converting natural language to typed operations without exposing tools to the classifier.
- Packaging a real ADK multi-agent application for Agent Engine while keeping its Tool Server private.
- Preserving service-to-service identity across public web, private control, managed agent runtime, and private tools.
- Making deterministic reset coexist with durable Firestore evidence.
- Showing execution proof without exposing raw commands, credentials, or chain-of-thought.
- Separating autonomous work from consequential mutation authority without turning the workflow into manual guidance.

## What's next

Future work could add explicitly authorized production integrations and more typed intents for locations, weather, equipment, and richer constraint solving. Those are roadmap items, not claims about the current contest build. The current product intentionally exposes only its verified narrow allowlist.

## Technical evidence

- `services/api/command_router.py`
- `tests/unit/test_production_command_router.py`
- `docs/evidence/agent-engine-cloud-3b.json`
- `docs/evidence/cloud-demo-3c/deployment.json`
- `docs/evidence/cloud-demo-3c/browser-verification.md`
- `docs/all-things-agentic/architecture.mmd`
- `docs/all-things-agentic/assets/studiogrid-architecture.png`
- `tests/unit/test_agent_engine_cloud.py`
- `tests/unit/test_approval_gates.py`
- `tests/unit/test_tool_authorization.py`
