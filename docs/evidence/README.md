# StudioGrid AI — Contest Evidence

This directory contains evidence of **real** development and execution actions
for the Google Agentic Cinema contest submission.

No evidence is backdated, fabricated, or mocked.

---

## Evidence Categories

Evidence files are added as the project is built and deployed.

### `ibm_bob/`
IBM Bob development session evidence.
- Session summaries (sanitized, no credentials)
- File creation logs
- Build/test results from Bob sessions

### `gemini/`
Real Gemini execution traces (Phase 2).
- Sanitized JSON execution traces
- Agent execution records (`AgentExecution` schema)
- Tool call records
- No API keys, no private data

### `agent_builder/`
Google Cloud Agent Builder execution logs (Phase 2).
- Agent run records
- Tool call sequences
- Correlation IDs

### `cloud/`
Cloud Run deployment evidence (Phase 2).
- Deployment screenshots
- Cloud Run service URLs
- Build logs (sanitized)

### `tests/`
Test run results.
- pytest output
- Vitest output
- Coverage reports

### `demo/`
Demo scenario execution evidence.
- Demo day scenario run
- Schedule proposal approval trace
- Continuity alert resolution trace
- Wrap report generation

---

## Rules

1. **No credentials** — no API keys, tokens, passwords, private keys
2. **No key files** — no service account JSON, no gcloud credentials
3. **No private reasoning traces** — no internal model chain-of-thought
4. **Sanitized traces are acceptable** — execution IDs, tool names, schemas, results
5. **Screenshots of real execution are acceptable**
6. **No fabricated evidence** — if something is not yet implemented, that section is empty

---

## IBM Bob Development Evidence

Primary IBM Bob evidence: [`../IBM_BOB_DEVELOPMENT_LOG.md`](../IBM_BOB_DEVELOPMENT_LOG.md)

The log records every real action taken by IBM Bob during development:
- Files created
- Commands executed
- Tests run
- Architecture decisions made

---

## Blocking Compliance Question

**Status: UNRESOLVED — requires user action**

> "Does demonstrated IBM Bob usage satisfy the IBM partner-service requirement,
> or must the runtime also call a specific IBM MCP / IBM service / IBM API
> at contest submission time?"

This question must be answered from official contest resources before
any IBM runtime integration is implemented.
