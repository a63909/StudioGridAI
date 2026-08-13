# StudioGrid AI — Architecture

## Overview

StudioGrid AI is an event-driven, multi-agent production control system for film shoots.
It continuously tracks planned vs actual shooting state, detects problems, forecasts
consequences, and proposes next best actions — always subject to human approval.

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend — Next.js / TypeScript (Cloud Run)                │
│  Dashboard · Timeline · Scene Board · Coverage              │
│  Continuity · Schedule · Report                             │
└────────────────────────┬────────────────────────────────────┘
                         │ REST + SSE (HTTPS)
┌────────────────────────▼────────────────────────────────────┐
│  FastAPI Tool Server (Cloud Run)                            │
│  Tool Registry · Approval Gates · Schema Validation         │
│  Audit Logger · SSE Event Stream                            │
└──────────┬──────────────────────────┬───────────────────────┘
           │ tool calls only          │ ADC (no key files)
┌──────────▼──────────┐   ┌──────────▼───────────────────────┐
│  Google ADK         │   │  Firestore                       │
│  Gemini 3.6 Flash   │   │  Cloud Logging / Trace           │
│  Orchestrator       │   │  Secret Manager                  │
│                     │   │  Cloud Storage                   │
│  SCHEDULE_AGENT     │   └──────────────────────────────────┘
│  COVERAGE_AGENT     │
│  CONTINUITY_AGENT   │   Phase 1: LocalStateStore (in-memory)
│  RISK_AGENT         │   Phase 1: LocalEventBus (in-process)
│  WRAP_REPORT_AGENT  │
└─────────────────────┘
```

## Key Principles

### 1. FACT / INFERENCE / RECOMMENDATION / HUMAN_DECISION

These four categories are always kept separate and visually distinct in the UI.

- **FACT**: Recorded evidence (e.g., Maya Reed reported unavailable until 11:30)
- **INFERENCE**: AI-derived conclusion (e.g., Scenes 14 and 18 cannot currently be shot)
- **RECOMMENDATION**: Agent proposal (e.g., Advance Scene 22)
- **HUMAN_DECISION**: Explicit human approval or rejection

### 2. Agents Never Mutate State Directly

All state changes flow through:
```
Agent → Tool Call → Tool Registry → Authorization Check →
Approval Gate → Schema Validation → State Store → Audit Log
```

### 3. Human Approval Gates

No schedule change, continuity override, or critical risk resolution
happens without explicit human confirmation.

### 4. Event-Driven Architecture

All state changes are triggered by typed `ProductionEvent` objects.
The Event Bus dispatches to all subscribed agents. Events are immutable.

## Agent Architecture

| Agent | Responsibility |
|-------|----------------|
| PRODUCTION_ORCHESTRATOR | Coordinates all agents, routes events |
| SCRIPT_BREAKDOWN_AGENT | Parses production package into typed domain model |
| SCHEDULE_AGENT | Detects conflicts, creates schedule proposals |
| COVERAGE_AGENT | Tracks planned vs completed shots, creates coverage alerts |
| CONTINUITY_AGENT | Detects continuity conflicts between shots |
| PRODUCTION_RISK_AGENT | Aggregates and prioritizes production risks |
| WRAP_REPORT_AGENT | Generates end-of-day report from actual state |

## Google Cloud Stack (Phase 2)

| Service | Purpose |
|---------|---------|
| Gemini | LLM inference for all agents |
| Google ADK | Real local multi-agent orchestration |
| Vertex AI Agent Engine | Prepared `AdkApp`; deployment pending IAM confirmation |
| Cloud Run | FastAPI tool server + Next.js frontend |
| Firestore | Production state storage |
| Cloud Logging | Structured audit trail with correlation IDs |
| Secret Manager | Partner credentials only |
| Cloud Storage | Production assets |
| IAM + ADC | Authentication — no key files |

## Phase 1 vs Phase 2

| Capability | Phase 1 | Phase 2 |
|-----------|---------|---------|
| Domain model | ✅ Complete | ✅ |
| Event system | ✅ LocalEventBus | Cloud Pub/Sub |
| Agents | ✅ Deterministic | ✅ Real Gemini 3.6 Flash + Google ADK |
| State store | ✅ In-memory | ✅ Firestore durable mirror |
| Dashboard | ✅ Deterministic status | ✅ Honest live runtime status |
| Cloud Run | ❌ | ✅ |
| Partner integration | NOT_CONFIGURED | TBD after requirement confirmed |

## ADR Index

- [ADR 001 — Event-Driven State](docs/adr/001-event-driven-state.md)
- [ADR 002 — Agent Interfaces](docs/adr/002-agent-interfaces.md)
- [ADR 003 — Human Approval Gates](docs/adr/003-human-approval-gates.md)
- [ADR 005 — Google ADK and Vertex AI Agent Runtime](docs/adr/005-google-agent-runtime-integration.md)

## Demo Film

**LAST LIGHT** — a fully original synthetic film production dataset.
All characters, actors, locations, and props are fictional.
No real IP, no existing scripts, no protected content.
