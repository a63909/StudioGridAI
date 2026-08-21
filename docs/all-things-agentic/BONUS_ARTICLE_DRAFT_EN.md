# Building an AI production control room with bounded authority

> **Hackathon disclosure:** I created this article for the purpose of entering the All Things Agentic Hackathon.

A shooting schedule looks like a list, but a production day behaves like a live constraint system. An actor delay affects every scene that needs that performer. A replacement scene may depend on work that is not complete. A location may have a limited window. An exterior may lose usable light. Coverage that looks complete at the scene level may still be missing required shots.

The operational problem is not generating a new paragraph of advice. It is deciding what work is actually eligible, producing a concrete change, preserving the evidence, and controlling who may apply it.

That is the problem behind StudioGrid AI, an AI Production Control Room built for the All Things Agentic Hackathon's Taskmaster category.

## From event to action

The demo uses an original fictional film package called LAST LIGHT. Its actors, scenes, locations, shots, dependencies, and schedule are structured synthetic data.

The golden event is deliberately small: Maya Reed is delayed by 45 minutes. The effect is not small. StudioGrid sends a structured `ACTOR_DELAYED` event through a deployed Google ADK application on Vertex AI Agent Engine. A Production Orchestrator routes it to the Schedule Agent. Gemini 3.6 Flash reasons over server-built production context, including actor-scene relationships, current schedule order, candidate scenes, locations, dependencies, and daylight constraints.

The agent then calls a typed `create_schedule_proposal` tool. It does not simply return text. The private Tool Server validates the proposal, confirms that its scene references are real, requires its initial status to be PENDING, persists it in Firestore, and records safe execution evidence.

The resulting proposal explains why a reorder is useful, which facts support it, which scenes are affected, the expected benefit, the risks, and confidence. A second workflow sends actual planned/completed shot state to a Coverage Agent, which identifies SH_12 and SH_13 as missing and persists an alert.

## Autonomy is not the same as authority

The hardest design decision was where autonomous work should stop.

We wanted the agent to do the heavy lifting: route the event, analyze constraints, select an eligible action, call a tool, and create a durable result. We did not want a probabilistic system to unilaterally change the call sheet for an entire crew.

StudioGrid therefore separates proposal authority from mutation authority. Agents receive tools that create PENDING recommendations. They do not receive the human approve/reject capability. The server-side approval gate also checks caller type, so a model cannot gain approval authority by following injected text.

The production manager is not guiding each reasoning step. They make one explicit decision at the consequential boundary. If they approve, the Control API applies the already-defined reorder and writes a `HUMAN_DECISION` event. If they reject, the schedule remains unchanged and the rejection is recorded.

This distinction made the architecture safer and, surprisingly, more agentic. The agent owns the operational workflow. The human owns accountability for a high-impact mutation.

## A public/private Google Cloud path

The browser reaches a public Next.js service on Cloud Run. It never receives a private backend URL or credential. A server-side BFF accepts only fixed demo actions and obtains a Google ID token for an IAM-private Control API.

The Control API invokes the deployed Vertex AI Agent Engine application. Agent Engine uses its own runtime identity to call a second IAM-private Cloud Run service that exposes typed agent tools. That service is the only agent path to Firestore.

The separation creates several useful boundaries:

- the public browser cannot call private control or tool services directly;
- the web identity can invoke Control, but not act as an agent tool caller;
- the Agent Engine identity can invoke the Tool Server, but cannot approve a human decision;
- agents never receive direct database access;
- Firestore stores durable application state and evidence, not hidden chain-of-thought.

## Defending the authority boundary

Prompt-injection defense starts before the model. The public API schema accepts a short allowlist: reset, fixed actor-delay events, approve/reject a known proposal, and coverage check. Additional fields such as an arbitrary `prompt` are forbidden.

But input filtering is not the main safety control. The important defense is deterministic and server-side. Even if an agent were induced to request `approve_schedule_proposal`, the Tool Registry and Approval Gate reject AGENT and SYSTEM callers. Unit tests exercise that exact case.

Failure handling follows the same pattern. A cloud probe asked the agent path to act on a nonexistent scene. The tool rejected it, an ERROR execution trace was stored, and the proposal count did not change. “No mutation” is the success condition for that failure test.

## What durable proof changed

Early agent demos can be convincing while they are running and impossible to audit afterward. StudioGrid treats evidence as part of the product behavior.

Every safe execution record can include an agent name, model name, execution ID, correlation ID, duration, typed tool name, result status, and evidence references. It deliberately excludes credentials, raw prompts, and chain-of-thought. The UI exposes enough metadata for a judge to connect the visible proposal to a real remote Agent Engine run without turning internal model context into a data leak.

Firestore also makes the operational outcome visible. After a human approves a schedule proposal, a browser refresh shows the same approved record, reordered schedule, and `HUMAN_DECISION` timeline. That persistence is stronger proof than an animation that only exists in one client session.

## What we learned

Three lessons stand out.

First, the most useful agent boundary is often not “human or no human.” It is “what work can the agent complete, and which authority should remain deterministic?”

Second, tools should express business capabilities, not generic database access. `create_schedule_proposal` and `create_coverage_alert` are narrow enough to validate and audit. A general write tool would make the system harder to reason about.

Third, demo readiness is an architectural property. A public URL, private service identities, durable state, failure-safe behavior, reproducible setup, and visible cloud proof all had to agree with the story.

StudioGrid AI does not generate a film plan. It helps a production adapt when the real day diverges from that plan—and it makes the line between agent action and human authority explicit.

Public demo: <https://studiogrid-web-729921508335.europe-west3.run.app>
