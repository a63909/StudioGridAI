# Building an AI production control room with bounded authority

> **Hackathon disclosure:** I created this article for the purpose of entering the All Things Agentic Hackathon.

A shooting schedule looks like a list, but a production day behaves like a live constraint system. An actor delay affects every scene that needs that performer. A replacement scene may depend on work that is not complete. A location may have a limited window. An exterior may lose usable light. Coverage that looks complete at the scene level may still be missing required shots.

The operational problem is not generating a new paragraph of advice. It is deciding what work is actually eligible, producing a concrete change, preserving the evidence, and controlling who may apply it.

That is the problem behind StudioGrid AI, an AI Production Control Room built for the All Things Agentic Hackathon's Taskmaster category.

## From one goal to action

The demo uses an original fictional film package called LAST LIGHT. Its actors, scenes, locations, shots, dependencies, and schedule are structured synthetic data.

The primary command is deliberately simple: “Check SC_05 and make sure all required coverage is complete.” The user does not choose a workflow or specify tool calls. A tool-less Gemini 3.6 Flash classifier maps the untrusted language to `CHECK_COVERAGE`; strict Pydantic validation accepts only the narrow typed route. The raw command stops there.

The private Control API invokes a deployed Google ADK application on Vertex AI Agent Engine. Its Production Orchestrator delegates the typed operation to the Coverage Agent. The specialist receives server-built planned/completed shot state, identifies `SH_12` and `SH_13` as missing, and calls `create_coverage_alert` on an IAM-private Tool Server. Firestore persists the OPEN alert and safe execution evidence. No second user action is required.

A second command—“Maya Reed is 45 minutes late. Keep today's shoot on schedule.”—routes the exact allowlisted fact to the Schedule Agent. Gemini reasons over actor-scene relationships, schedule order, candidates, locations, dependencies, and daylight. The resulting PENDING proposal explains the reorder, evidence, affected scenes, expected benefit, risks, and confidence.

## Autonomy is not the same as authority

The hardest design decision was where autonomous work should stop.

We wanted the agent to do the heavy lifting: route the event, analyze constraints, select an eligible action, call a tool, and create a durable result. We did not want a probabilistic system to unilaterally change the call sheet for an entire crew.

StudioGrid therefore separates proposal authority from mutation authority. Agents receive tools that create PENDING recommendations. They do not receive the human approve/reject capability. The server-side approval gate also checks caller type, so a model cannot gain approval authority by following injected text.

The production manager is not guiding each reasoning step. They make one explicit decision at the consequential boundary. If they approve, the Control API applies the already-defined reorder and writes a `HUMAN_DECISION` event. If they reject, the schedule remains unchanged and the rejection is recorded.

This distinction made the architecture safer and, surprisingly, more agentic. The agent owns the operational workflow. The human owns accountability for a high-impact mutation.

## A public/private Google Cloud path

The browser reaches a public Next.js service on Cloud Run. It never receives a private backend credential. A server-side BFF accepts a bounded natural-language command, applies request limits, and obtains a Google ID token for an IAM-private Control API.

Inside Control, a Gemini classifier with no tools and no mutation authority returns only `ACTOR_DELAY`, `CHECK_COVERAGE`, or `UNSUPPORTED`. Pydantic validates that output before Control invokes the deployed Vertex AI Agent Engine application. Agent Engine uses its own runtime identity to call a second IAM-private Cloud Run service that exposes typed agent tools. That service is the only agent path to Firestore.

The separation creates several useful boundaries:

- the public browser cannot call private control or tool services directly;
- the web identity can invoke Control, but not act as an agent tool caller;
- the Agent Engine identity can invoke the Tool Server, but cannot approve a human decision;
- agents never receive direct database access;
- Firestore stores durable application state and evidence, not hidden chain-of-thought.

## Defending the authority boundary

The public UI does accept natural-language production commands, but raw language reaches only an isolated classifier. The classifier has no tools, cannot mutate state, cannot call the Tool Server, and is instructed to treat the command as untrusted data. Its structured output must pass a strict typed allowlist; unsupported and invalid routes never reach a specialist.

Specialists receive only the typed operation and server-built production context, never the raw command. The consequential defense is also deterministic and server-side: even if a specialist were compromised, the Tool Registry and Approval Gate reject AGENT and SYSTEM callers attempting schedule approval or rejection. Unit tests exercise that exact case.

Failure handling follows the same pattern. A cloud probe asked the agent path to act on a nonexistent scene. The tool rejected it, an ERROR execution trace was stored, and the proposal count did not change. “No mutation” is the success condition for that failure test.

## What durable proof changed

Early agent demos can be convincing while they are running and impossible to audit afterward. StudioGrid treats evidence as part of the product behavior.

Every safe execution record can include an agent name, model name, execution ID, correlation ID, duration, typed tool name, result status, and evidence references. It deliberately excludes credentials, raw commands, specialist prompts, and chain-of-thought. The UI exposes enough metadata for a judge to connect the visible result to a real remote Agent Engine run without turning internal model context into a data leak.

Firestore also makes the operational outcome visible. After a human approves a schedule proposal, a browser refresh shows the same approved record, reordered schedule, and `HUMAN_DECISION` timeline. That persistence is stronger proof than an animation that only exists in one client session.

## What we learned

Three lessons stand out.

First, the most useful agent boundary is often not “human or no human.” It is “what work can the agent complete, and which authority should remain deterministic?”

Second, tools should express business capabilities, not generic database access. `create_schedule_proposal` and `create_coverage_alert` are narrow enough to validate and audit. A general write tool would make the system harder to reason about.

Third, demo readiness is an architectural property. A public URL, private service identities, durable state, failure-safe behavior, reproducible setup, and visible cloud proof all had to agree with the story.

StudioGrid AI does not generate a film plan. It helps a production adapt when the real day diverges from that plan—and it makes the line between agent action and human authority explicit.

Public demo: <https://studiogrid-web-729921508335.europe-west3.run.app>
