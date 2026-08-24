# The Taskmaster judging strategy

StudioGrid's memorable idea is simple: **Give StudioGrid the production problem, not the steps.** A film production day is a live constraint system; StudioGrid safely turns one bounded natural-language goal into an operational result.

## First 20 seconds

Show the public `.run.app` URL and say:

> I will give StudioGrid one production goal: check whether SC_05 has every required shot. A tool-less Gemini router validates the goal, then a real Google ADK agent on Vertex AI Agent Engine inspects production state, calls a private typed tool, and persists the result. I do not guide any intermediate step.

Do not open with a framework list or the Schedule approval flow.

## Innovation & Operational Utility — 40%

### Primary proof: one-command Coverage

1. Click **Reset Demo** if needed.
2. Enter `Check SC_05 and make sure all required coverage is complete.`
3. Keep the live execution visible without cuts or speed-up.
4. Show the autonomous result: `SC_05`, `1/3`, `33.3%`, missing `SH_12` / `SH_13`, and an `OPEN` alert.
5. Expand Technical details and show routing intent, Coverage Agent, model, execution ID, and typed tool evidence.
6. State explicitly: no follow-up click was required after the command.

### Secondary proof: Schedule authority boundary

1. Reset and enter `Maya Reed is 45 minutes late. Keep today's shoot on schedule.`
2. Show the resulting PENDING recommendation with evidence, affected scenes, expected benefit, risks, confidence, and proposed order.
3. Point out that the current schedule remains unchanged.
4. Explain that the agent has completed its work; a human only authorizes or rejects the consequential mutation.
5. Optionally approve once and show before/after plus durable `HUMAN_DECISION`.

### Message

Coverage is the clean Taskmaster proof: one goal → autonomous routing → specialist reasoning → typed tool call → durable operational result.

Schedule proves that **autonomy is not the same as authority**. The human does not route agents, enumerate constraints, choose a scene, or construct the recommendation. Approval is not manual orchestration; it is an explicit transfer of authority for a high-impact production change.

## Architectural Discipline & Tech Stack — 30%

### Show, do not merely name

- **Safe language boundary:** raw user language reaches only a Gemini 3.6 Flash classifier with no tools and no mutation authority.
- **Typed validation:** Pydantic permits only `ACTOR_DELAY`, `CHECK_COVERAGE`, or `UNSUPPORTED`; invalid output and unsupported commands fail closed.
- **Context isolation:** Schedule and Coverage receive server-built typed production state, never the raw command.
- **Decoupling:** public Next.js web, IAM-private Control API, Vertex AI Agent Engine, IAM-private Tool Server, Firestore.
- **Agent separation:** Google ADK Production Orchestrator delegates to Schedule Agent or Coverage Agent.
- **Scoped tools:** specialists receive typed create operations; they do not receive approval authority.
- **State:** alerts, proposals, execution metadata, events, demo sessions, and schedule state persist in Firestore.
- **Identity:** the BFF obtains an ID token for Control; Agent Engine invokes the Tool Server with its runtime identity.
- **Authority defense:** server-side `ApprovalGate` blocks AGENT/SYSTEM approval even if model behavior is compromised.
- **Failure handling:** unsupported routes and invalid mutations produce no specialist action or consequential state change.
- **Observability:** safe execution/correlation IDs plus Cloud Trace; raw commands, credentials, and chain-of-thought are not exposed.

### Architecture proof order

Use the rendered architecture diagram first. Trace language only to the isolated Command Router and typed validation, then trace the typed operation through Agent Engine, ADK specialists, private tools, and Firestore. Show the human Schedule path separately.

## Demo & Production Readiness — 30%

### Proof hierarchy

1. Public `.run.app` URL.
2. One continuous, unedited Coverage command and durable `OPEN` result.
3. Safe technical execution ID and all four connected runtime services.
4. Schedule command producing a PENDING proposal with the unchanged schedule.
5. Optional human approval, before/after, and refresh persistence.
6. Cloud proof: Agent Engine resource, Cloud Run public/private split, Firestore record.
7. Repository: current diagram, exact spin-up instructions, routing tests, and cloud evidence.

### Avoid

- Looking for removed Maya/Daniel/Coverage workflow buttons.
- Describing StudioGrid as understanding arbitrary production commands.
- Calling the Command Router a tool-enabled agent.
- Sending raw language directly to Schedule or Coverage in the explanation.
- A code walkthrough or architecture jargon before the production problem.
- Implying background monitoring or integrations the public build does not implement.
- Calling Firestore persistence “agent memory.”
- Claiming customers, measured savings, or a real-studio deployment.

## Risk response: human approval in a Taskmaster entry

Use this answer:

> Coverage completes a full operational workflow after one natural-language command, with no additional human action. Schedule also completes routing, analysis, tool execution, evidence, and proposal persistence autonomously. Human approval is intentionally outside the agent's authority because changing a real shooting order affects an entire crew. Autonomy is the ability to do the work; authority is permission to apply a consequential mutation.

## Final judge sequence

1. Problem: film production is a live constraint system.
2. Promise: give StudioGrid the problem, not the steps.
3. Taskmaster proof: one Coverage command → `OPEN` durable result.
4. Safety proof: tool-less router → strict typed validation → raw command stops.
5. Second workflow: one Schedule command → PENDING evidence-backed proposal.
6. Authority boundary: agent may propose; human alone may approve/reject.
7. Cloud proof and architecture.
8. End on operational value, not model branding.
