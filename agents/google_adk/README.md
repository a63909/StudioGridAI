# Google ADK runtime

This package contains the real StudioGrid AI Google runtime:

- `PRODUCTION_ORCHESTRATOR`: Google ADK routing root. Local single-route
  adapters use `SequentialAgent`; Agent Engine uses one `LlmAgent` with both
  specialists.
- `SCHEDULE_AGENT`: Gemini 3.6 Flash specialist with only
  `create_schedule_proposal`.
- `COVERAGE_AGENT`: Gemini 3.6 Flash specialist with only
  `create_coverage_alert`.
- FastAPI typed-tool gateway; agents never access Firestore directly.
- Safe operational traces without chain-of-thought.

Verified configuration (2026-08-13):

```text
project: studiogrid-ai
model: gemini-3.6-flash
model endpoint: global
Agent Engine region: europe-west3
Firestore database: (default)
demo namespace: productions/last-light-demo
authentication: Application Default Credentials
```

Run the full local smoke after ADC is configured:

```powershell
python -m agents.google_adk.smoke_schedule
```

The command starts a local FastAPI server, performs two real actor-delay
scenarios (Maya Reed and Daniel Osei), verifies typed tool calls, Firestore,
human approval, schedule mutation, and timeline audit, then stops the server.
It does not deploy or delete any cloud data.

Inspect or create the managed Agent Engine resource:

```powershell
python -m agents.google_adk.deploy_agent_engine --list-only
python -m agents.google_adk.deploy_agent_engine
```

Run the remote async-session smoke and retain safe evidence:

```powershell
python -m agents.google_adk.smoke_agent_engine `
  --resource projects/studiogrid-ai/locations/europe-west3/reasoningEngines/ID `
  --evidence-out docs/evidence/agent-engine-cloud-3b.json
```

The remote smoke covers Maya (`ACT_02`, 45 minutes), Daniel (`ACT_03`, 30
minutes), Coverage Agent, Agent Engine session get/list, Firestore PENDING and
trace records, and an authoritative Tool Server rejection with no false success
trace. It never approves a proposal and never deletes the Agent Engine.

Architecture and official sources are recorded in
`docs/adr/005-google-agent-runtime-integration.md` and
`docs/adr/007-vertex-agent-engine-cloud-runtime.md`.
