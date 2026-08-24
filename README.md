# StudioGrid AI

**AI Production Control Room** — a deployed multi-agent control plane for film-production operations.

> **Give StudioGrid the production problem, not the steps.** One natural-language command enters a narrow, fail-closed routing boundary and starts the corresponding operational workflow. The agent acts autonomously where it has authority; a human approves only consequential schedule mutations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Cloud demo](https://img.shields.io/badge/Cloud%20demo-PUBLIC-blue)](https://studiogrid-web-729921508335.europe-west3.run.app)
![AI](https://img.shields.io/badge/AI-Gemini%203.6%20Flash-green)
![Agent runtime](https://img.shields.io/badge/Runtime-Vertex%20AI%20Agent%20Engine-purple)

## Quick judge path

Hosted demo: **<https://studiogrid-web-729921508335.europe-west3.run.app>**

1. Open the hosted demo and click **Reset Demo** if needed.
2. In **What happened or what needs to be done?**, enter:

   > Check SC_05 and make sure all required coverage is complete.

3. StudioGrid classifies the goal, routes `CHECK_COVERAGE` to the deployed Coverage Agent, inspects the current production state, calls the typed private tool, and persists the result—without another user action.
4. Inspect `SC_05`, `1/3` completed shots, `33.3%`, missing `SH_12` / `SH_13`, the `OPEN` alert, connected runtime statuses, and the execution ID inside **Technical details**.
5. Reset, then enter:

   > Maya Reed is 45 minutes late. Keep today's shoot on schedule.

6. Wait for the real Schedule Agent to create a **PENDING** recommendation with evidence, expected benefit, risks, confidence, affected scenes, and a proposed order. The current schedule remains unchanged.
7. Optionally use **Approve as human** or **Reject as human** to see the consequential authority boundary, persistence, and `HUMAN_DECISION` audit trail.

The demo uses the fictional film **LAST LIGHT**, original synthetic production data, and no real customer information. No localhost or sign-in is required for the hosted judge path.

### Why this is The Taskmaster when Schedule requires approval

Coverage is the clean end-to-end Taskmaster proof: **one natural-language goal → safe routing → agent reasoning → typed tool call → durable operational result**. No follow-up click is required.

Schedule demonstrates a separate production discipline: **autonomy is not the same as authority**. The agent completes routing, constraint analysis, recommendation construction, tool execution, and persistence autonomously. The human does not choose scenes or guide the solution; they only authorize or reject the already-defined high-impact mutation.

## What StudioGrid does

A film production day is a live constraint system. Actor availability, scene dependencies, location windows, daylight, completed work, and missing shots interact. Traditional tools record a schedule; StudioGrid performs a bounded operational workflow when reality changes.

The operator states one production goal in natural language. An isolated Gemini 3.6 Flash classifier with **no tools and no mutation authority** maps that untrusted language to a strict typed allowlist. Only the validated operation enters the existing cloud workflow; specialist agents never receive the raw command.

For the primary Coverage workflow, the Google ADK Production Orchestrator delegates `CHECK_COVERAGE` to the Coverage Agent. It compares planned and completed shots for `SC_05`, finds `SH_12` and `SH_13` missing, calls `create_coverage_alert`, and persists an `OPEN` alert plus safe execution evidence in Firestore—all after one command.

For an allowed actor delay, the Orchestrator delegates a typed `ACTOR_DELAYED` fact to the Schedule Agent. The agent evaluates current constraints, invokes `create_schedule_proposal`, and persists a **PENDING** recommendation. Approval applies the already-defined reorder and records `HUMAN_DECISION`; rejection leaves the schedule unchanged.

## FACT / INFERENCE / RECOMMENDATION / HUMAN_DECISION

| Category | Example |
|---|---|
| **FACT** | Maya Reed is reported delayed by 45 minutes |
| **INFERENCE** | Actor-dependent scenes are temporarily blocked |
| **RECOMMENDATION** | Reorder specific eligible scenes |
| **HUMAN_DECISION** | Production Manager approved or rejected the proposal |

The UI and data model keep these categories distinct so model conclusions are not presented as observed facts.

## Verified cloud architecture

![StudioGrid architecture](docs/all-things-agentic/assets/studiogrid-architecture.png)

```text
Public browser
  → public Cloud Run: studiogrid-web
  → server-side authenticated BFF
  → IAM-private Cloud Run: studiogrid-control-api
      → tool-less Gemini 3.6 Flash Command Router
      → strict typed allowlist / Pydantic validation
      → typed operation only
  → Vertex AI Agent Engine
  → Google ADK Production Orchestrator
      ├─ Schedule Agent
      └─ Coverage Agent
  → Gemini 3.6 Flash specialist reasoning over server-built context
  → typed authenticated tools
  → IAM-private Cloud Run: studiogrid-tool-server
  → Firestore

PENDING proposal → HUMAN APPROVE / REJECT → Control API → durable mutation/audit
```

The Command Router is a classifier, not a tool-enabled agent. It cannot call the Tool Server, cannot mutate production state, and cannot grant itself new capabilities. Unsupported location, weather, equipment, arbitrary mutation, approval-bypass, and non-allowlisted actor-delay commands fail closed before any specialist workflow runs.

| Google technology | Current use |
|---|---|
| **Gemini 3.6 Flash** | Tool-less command classification plus specialist reasoning over server-built production context |
| **Google ADK 2.6.3** | Production Orchestrator and Schedule/Coverage specialist graph |
| **Vertex AI Agent Engine** | Deployed remote ADK application in `europe-west3` |
| **Cloud Run** | Public Next.js web plus two IAM-private Python services |
| **Firestore** | Demo state, proposals, alerts, events, sessions, and safe execution evidence |
| **Cloud Trace** | Sampled cloud trace and execution correlation evidence |

Agent Engine resource:

```text
projects/729921508335/locations/europe-west3/reasoningEngines/5132986471388545024
```

## Agent responsibilities

| Agent | Responsibility |
|---|---|
| `PRODUCTION_ORCHESTRATOR` | Routes validated typed production events to a specialist |
| `SCHEDULE_AGENT` | Evaluates actor, scene, location, dependency, timing, and daylight constraints; creates PENDING schedule proposals |
| `COVERAGE_AGENT` | Compares planned/completed shots and creates coverage alerts |

Phase 1 deterministic agents for continuity, risk, and wrap reporting remain in the repository, but the public cloud golden path claims only the remotely verified Production Orchestrator, Schedule Agent, and Coverage Agent.

## Authority and security boundaries

- The browser reaches only the public web service.
- The public UI accepts bounded natural-language production commands; the Next.js BFF caps request size, rate-limits actions, and obtains a server-side Google ID token for the private Control API.
- Raw user language reaches only the isolated Gemini Command Router. The router has no tools, no mutation authority, and no path to call the Tool Server.
- Router output is validated by strict Pydantic models against `ACTOR_DELAY`, `CHECK_COVERAGE`, or `UNSUPPORTED`; only the resulting typed operation is passed onward.
- Schedule and Coverage specialists receive server-built production context, not the raw command. Unsupported commands fail closed.
- Agent Engine calls a separate private Tool Server with its runtime identity.
- Agents never access Firestore directly.
- Tool inputs and state transitions are validated with Pydantic schemas.
- Agent proposals must be PENDING and reference known scenes.
- `ApprovalGate` permits only HUMAN callers to approve/reject schedule proposals.
- ADC/service identities are used; service-account JSON keys are neither required nor committed.
- Safe evidence excludes credentials, raw prompts, and chain-of-thought.

See [SECURITY.md](SECURITY.md) and [architecture.mmd](docs/all-things-agentic/architecture.mmd).

## Repository layout

```text
agents/                         Google ADK and deterministic agent implementations
apps/web/                       Next.js public web/BFF
demo/last_light/                Synthetic LAST LIGHT production package
docs/adr/                       Architecture decisions
docs/evidence/                  Safe verified cloud evidence
docs/all-things-agentic/        Submission copy, diagram, video, and judging evidence
services/api/                   FastAPI Control API and Tool Server code
tests/                          Backend tests
```

## Reproducibility and spin-up

### Requirements

- Git
- Python **3.11+** (Cloud Run image uses Python 3.12)
- Node.js **22.12+** and npm (web image uses Node 22)
- Optional: Docker
- For real cloud mode: a Google Cloud project with billing, `gcloud`, ADC or workload identity, and permission to create/configure the resources described below

Clone the repository using the URL supplied in the Devpost entry, then run all commands from the repository root unless a step says otherwise.

### 1. Local deterministic API

This path requires no Google Cloud account and loads the synthetic LAST LIGHT package into the local state store.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e "services/api[dev]"
python -m uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/health`. With cloud flags left false, the API reports deterministic DEV mode.

### 2. Frontend development

```bash
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:3000/en/dashboard`.

The cloud-demo dashboard route intentionally uses the authenticated server-side BFF. To make its Production Command workflow operational, configure `CONTROL_API_URL` and `CONTROL_API_AUDIENCE` to the same HTTPS private Control API URL and run the Next.js server under a Google identity that already has `run.invoker` on that exact service. Do not expose these variables with a `NEXT_PUBLIC_` prefix and do not use service-account key files.

The easiest judge path is the hosted public URL above. External evaluators are not expected to receive IAM access to private services.

### 3. Environment variables

Copy `.env.example` only for local development:

```bash
cp .env.example .env.local
```

On Windows PowerShell use `Copy-Item .env.example .env.local`. Never commit `.env.local`.

Important real-runtime variables:

| Variable | Purpose |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI model location (`global` in the verified deployment) |
| `GOOGLE_CLOUD_AGENT_ENGINE_LOCATION` | Agent Engine region (`europe-west3`) |
| `GEMINI_MODEL` | `gemini-3.6-flash` |
| `STUDIOGRID_AGENT_ENGINE_RESOURCE` | Deployed reasoning engine resource name |
| `STUDIOGRID_TOOL_SERVER_URL` | Private Tool Server HTTPS URL |
| `STUDIOGRID_TOOL_SERVER_AUTHENTICATED` | Require authenticated private tool calls |
| `STUDIOGRID_FIRESTORE_ENABLED` | Enable durable Firestore state |
| `STUDIOGRID_CONTROL_API_ONLY` | Restrict an API deployment to `/control/*` |
| `STUDIOGRID_AGENT_TOOL_SERVER_ONLY` | Restrict an API deployment to `/tools/agent/*` |
| `CONTROL_API_URL` / `CONTROL_API_AUDIENCE` | Server-only web BFF target and ID-token audience |

### 4. Google Cloud prerequisites

Use a project you control. Enable at least:

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com
```

Create a Firestore Native database and a staging Cloud Storage bucket in the chosen regions. Create separate runtime service accounts for Agent Engine, the web BFF, the Control API, and the Tool Server. Grant only the required scoped permissions:

- Agent runtime: invoke the exact private Tool Server and use required Vertex/telemetry services.
- Web runtime: invoke the exact private Control API only.
- Control runtime: invoke the exact Agent Engine resource, access the demo Firestore namespace, and write logs/traces.
- Tool runtime: access the demo Firestore namespace and write logs/traces.

Do not grant `allUsers` to the Control API or Tool Server. The verified deployment exposes only `studiogrid-web` publicly.

### 5. Deploy in dependency order

1. **Tool Server:** build the root `Dockerfile`; deploy with `STUDIOGRID_AGENT_TOOL_SERVER_ONLY=true`, Firestore enabled, and unauthenticated access disabled.
2. **Agent Engine:** update the constants in `agents/google_adk/deploy_agent_engine.py` for your project, bucket, runtime service account, and private Tool Server URL. From the repository root, install `agents/google_adk/requirements.agent_engine.txt`, authenticate with ADC, then run:

   ```bash
   python -m agents.google_adk.deploy_agent_engine
   ```

   The helper refuses to create a duplicate matching engine unless the explicit reuse/update option is used.
3. **Control API:** deploy the root image with `STUDIOGRID_CONTROL_API_ONLY=true`, Firestore enabled, the Agent Engine resource set, and unauthenticated access disabled.
4. **Web:** build from `apps/web/Dockerfile`; set server-only `CONTROL_API_URL` and `CONTROL_API_AUDIENCE`; deploy publicly under the web runtime identity.
5. Verify IAM boundaries before running the demo: public web returns 200; unauthenticated Control/Tool requests return 401/403.

The committed deployment helper is pinned to the verified StudioGrid resource values so it cannot be treated as a generic one-command installer. Review its constants before using another project. Never copy credentials into source files.

### 6. Seed/reset and real-agent checks

- Local API startup loads `demo/last_light/production_package.json`.
- The public demo **Reset Demo** action resets only the synthetic `last-light-demo` application state for the current demo session and preserves audit/evidence collections.
- `python -m agents.google_adk.smoke_schedule` runs the local real-agent milestone and requires ADC plus configured Google Cloud resources.
- Set `RESOURCE_NAME` to a reasoning-engine resource you own, then run `python -m agents.google_adk.smoke_agent_engine --resource "$RESOURCE_NAME"`; inspect `--help` first.

### 7. Validation

```bash
python -m pytest -q

cd apps/web
npm test
npm run lint
npm run typecheck
npm run build
```

## Evidence

- [Agent Engine cloud evidence](docs/evidence/agent-engine-cloud-3b.json)
- [Cloud demo deployment evidence](docs/evidence/cloud-demo-3c/deployment.json)
- [Browser verification](docs/evidence/cloud-demo-3c/browser-verification.md)
- [All Things Agentic official requirements](docs/all-things-agentic/OFFICIAL_REQUIREMENTS.md)
- [Project chronology](docs/all-things-agentic/PROJECT_CHRONOLOGY.md)
- [Video/live capture sequence](docs/all-things-agentic/LIVE_CAPTURE_SEQUENCE.md)

## Development assistance disclosure

AI coding assistants are permitted by the All Things Agentic Official Rules. StudioGrid used Codex during later development/submission preparation and preserves its historical IBM Bob Phase 1 development log in [docs/IBM_BOB_DEVELOPMENT_LOG.md](docs/IBM_BOB_DEVELOPMENT_LOG.md). Generated Phase 1 date metadata was corrected transparently; Git history retains the original text. See the chronology document for the evidence classification.

## Demo film — LAST LIGHT

LAST LIGHT is a fully original synthetic production package:

- 4 fictional actors
- 3 fictional locations
- 10 scenes and 22+ planned shots
- synthetic schedule, continuity, coverage, and actor-delay scenarios
- no customer data, licensed script, or real film-studio information

Fictional 2025 dates inside the production package are story data, not project chronology.

## Current limitations

- The public flow is a controlled synthetic demo, not a deployment at a real film studio.
- The public command surface is intentionally narrow: exact supported actor-delay demo facts and the fixed `SC_05` shot-coverage workflow. It does not claim general production-language understanding.
- Location, weather, equipment, arbitrary actor/delay, free-form mutation, and approval-bypass commands are unsupported and fail closed.
- The current product does not claim continuous ingestion from real call sheets, calendars, email, or IoT systems.
- The verified remote agent graph covers Schedule and Coverage workflows; other deterministic Phase 1 agents are not claimed as deployed cloud agents.
- Agent Engine scales from zero, so a cold request can take longer than a warm request.
- The deploy helper contains verified project-specific constants and requires review for another Google Cloud project.
- No measured cost savings, production adoption, customer partnerships, or legal-compliance certification is claimed.

## All Things Agentic Hackathon

- Primary category: **The Taskmaster**
- Mandatory model: PASS — Gemini 3.6 Flash through Vertex AI
- Google Agent Framework: PASS — Google ADK
- Google Cloud infrastructure: PASS — Cloud Run and Firestore (plus Agent Engine/Trace)
- Submission materials: [docs/all-things-agentic](docs/all-things-agentic)

Personal eligibility, ownership representations, repository publication, video upload, and final Devpost submission remain explicit entrant actions.
