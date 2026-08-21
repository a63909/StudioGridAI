# The Taskmaster judging strategy

StudioGrid's memorable idea is simple: **a film production day is a live constraint system**. Traditional tools record the plan; StudioGrid performs the operational work required when reality changes.

## First 20 seconds

Show the public `.run.app` URL and say:

> Maya Reed is 45 minutes late. StudioGrid does not answer with advice. A real ADK multi-agent system evaluates the live production state, creates an actionable schedule proposal, and persists the evidence. Only the consequential mutation waits for a human decision.

Do not open with a framework list.

## Innovation & Operational Utility — 40%

### What judges should see

1. Click **Simulate Maya delay — 45 min** once.
2. Do not provide the agent with a target scene or schedule answer.
3. Show the runtime moving through Vertex AI Agent Engine, Gemini, the Production Orchestrator, Schedule Agent, private typed tools, and Firestore.
4. Show the resulting PENDING recommendation with why, evidence, affected scenes, expected benefit, risks, and confidence.
5. Emphasize that the multi-step work is finished before the approval click.
6. Approve once; show real before/after ordering and durable `HUMAN_DECISION`.
7. Briefly show ACT_03/Daniel and Coverage as proof that the workflow is not a Maya-only script.

### Message

The human does not route agents, enumerate constraints, select a replacement scene, or construct a proposal. Human approval exists only at the high-impact state-mutation boundary. That is operational autonomy with bounded authority, not a manual chatbot flow.

### Strongest evidence

- `docs/evidence/agent-engine-cloud-3b.json`
- `docs/evidence/cloud-demo-3c/deployment.json`
- `agents/google_adk/production_context.py`
- `agents/google_adk/schedule_agent_real.py`
- `agents/google_adk/coverage_agent_real.py`
- Fresh live ACT_02/ACT_03/Coverage smoke

## Architectural Discipline & Tech Stack — 30%

### Show, do not merely name

- **Decoupling:** public Next.js web, IAM-private Control API, Vertex AI Agent Engine, IAM-private Tool Server, Firestore.
- **Agent separation:** Production Orchestrator routes to Schedule Agent or Coverage Agent.
- **Scoped tools:** agents receive typed create operations; they do not receive the human approve/reject authority.
- **State:** proposals, execution metadata, events, demo sessions, and schedule state persist in Firestore.
- **Identity:** server-side BFF obtains an ID token for the private Control API; Agent Engine calls the private Tool Server with its runtime identity.
- **Prompt-injection defense:** request schemas reject arbitrary prompt fields, and server-side `ApprovalGate` blocks AGENT/SYSTEM callers even if model instructions are compromised.
- **Failure handling:** invalid tool mutations produce `ToolServerError`, an ERROR execution trace, and zero proposal mutation.
- **Observability:** safe execution/correlation IDs plus Cloud Trace; prompts and chain-of-thought are not exposed.

### Architecture proof order

Use the rendered architecture diagram first, then show only three cloud views: Agent Engine resource, Cloud Run access boundary, Firestore persisted record. This is faster and clearer than touring every console page.

## Demo & Production Readiness — 30%

### Proof hierarchy

1. Public `.run.app` URL in the address bar.
2. One continuous, unedited ACT_02 action.
3. UI changes from FACT to PENDING to approved before/after state.
4. Refresh and show persistence.
5. Cloud proof: Agent Engine resource, Cloud Run public/private split, Firestore record.
6. Repository: diagram, exact spin-up instructions, evidence JSON, test results.

### Avoid

- A code walkthrough.
- Architecture jargon before the production problem.
- Implying background monitoring that the demo does not show.
- Calling Firestore persistence “agent memory.”
- Claiming real customers, measured savings, or film-studio deployment.
- Cutting away during the agent's live execution; the official rubric calls for unedited proof.

## Risk response: human approval in a Taskmaster entry

The official Taskmaster criterion favors completion without human intervention. Present the boundary precisely:

- The agent autonomously completes the interrupt-to-proposal workflow.
- Approval is not needed for agent routing, analysis, tool execution, evidence creation, or persistence.
- A schedule mutation affects an entire crew, so the agent deliberately lacks that authority.
- The human chooses APPROVE or REJECT; the Control API then performs the already-specified mutation and records the decision.

This makes the safety gate evidence of architectural discipline while preserving the high-autonomy story.

## Final judge sequence

1. Problem: a live constraint system.
2. Public live action: Maya delay.
3. Autonomous result: PENDING proposal with evidence.
4. Authority boundary: agent cannot approve.
5. Consequence: human approve → schedule changes → durable decision.
6. Breadth: Coverage Agent finds `SH_12`/`SH_13`; ACT_03 proves generic behavior.
7. Cloud proof and architecture.
8. End on operational value, not model branding.
