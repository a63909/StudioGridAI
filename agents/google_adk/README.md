# Google ADK runtime

This package contains the real StudioGrid AI Google runtime:

- `PRODUCTION_ORCHESTRATOR`: Google ADK `SequentialAgent` root.
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

Architecture and official sources are recorded in
`docs/adr/005-google-agent-runtime-integration.md`.
