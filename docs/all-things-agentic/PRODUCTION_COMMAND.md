# Production Command — Taskmaster entry point

## Purpose

The public StudioGrid demo now exposes one natural-language **Production Command** surface above the existing diagnostic controls. The operator states the production problem once; StudioGrid chooses one supported workflow and executes it through the same verified cloud control plane.

This is intentionally **not** an unrestricted chat-to-tools interface.

## Trust boundary

```text
untrusted natural-language command
  → public Cloud Run web/BFF
  → IAM-private Control API
  → Gemini 3.6 Flash command classifier (NO TOOLS)
  → strict Pydantic allowlist
      ├─ ACTOR_DELAY (exact demo facts only)
      ├─ CHECK_COVERAGE
      └─ UNSUPPORTED
  → existing typed Control API operation
  → Vertex AI Agent Engine
  → Google ADK Production Orchestrator
  → authorized specialist
  → IAM-private Tool Server
  → Firestore
```

The raw command stops at the no-tools classifier. It is not forwarded to the tool-enabled Schedule or Coverage agents, is not treated as production state, and is not persisted by the new routing layer.

## Supported public commands

### Coverage — end to end

Example:

> Check SC_05 and make sure all required coverage is complete.

Gemini maps the goal to `CHECK_COVERAGE`. The existing Control API establishes the fixed synthetic SH_11 demo fact, then the deployed ADK Coverage Agent compares actual planned/completed shot state, identifies the factual missing IDs, calls `create_coverage_alert`, and persists the OPEN alert and safe execution evidence. No second user decision is required.

This is the clearest Taskmaster path: one user goal → routing → specialist work → typed tool call → durable result.

### Schedule — autonomous work with a deliberate authority boundary

Example:

> Maya Reed is 45 minutes late. Keep today's shoot on schedule.

Gemini may map only the exact supported Maya 45-minute or Daniel 30-minute synthetic facts to `ACTOR_DELAY`. The existing Schedule Agent then performs the production analysis and creates a durable PENDING schedule proposal. The agent still cannot approve or reject its own proposal.

Applying a schedule mutation remains HUMAN-only because changing a shooting order affects crew, locations, and downstream departments. StudioGrid treats autonomy and authority as separate concerns.

## Fail-closed behavior

The public command router returns `UNSUPPORTED` for location outages, weather, equipment failures, arbitrary actor/delay combinations, free-form mutations, and requests to bypass approval. It does not silently coerce an unsupported command into a supported demo fact.

The existing direct demo buttons remain available as deterministic diagnostic shortcuts and evidence probes; the Production Command surface is the intended product-style entry point for judging.
