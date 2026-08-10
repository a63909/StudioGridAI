# StudioGrid AI

**An AI production control room for film shoots.**

> "An AI production control room that continuously understands what was planned,
> what has actually been shot, what changed on set, what is now at risk,
> and what the crew should do next."

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-1%20MVP-blue)]()
[![AI Status](https://img.shields.io/badge/AI-DEV%20MODE-orange)]()

---

## What StudioGrid AI Is

StudioGrid AI is **not** a chatbot. It is **not** a script generator. It is **not** a film generator.

It is a **coordination layer** for real film production: an intelligent dispatch system that
continuously tracks what was planned vs what was actually shot, detects problems as they happen,
and proposes the next best action — always subject to human approval.

It helps:
- Directors and First ADs
- Line Producers and Production Managers
- Script Supervisors
- Camera Crew
- Editorial

---

## The Problem

A single day of principal photography can cost $100,000+. When an actor is delayed,
a location becomes unavailable, or coverage turns out to be incomplete, production teams
currently rely on manual coordination and spreadsheets. Errors compound. Time is lost.

---

## Product Workflow

1. The shoot day starts with a **planned schedule** (18 shots, 10 scenes)
2. Events occur in real time: shots completed, actors delayed, locations warned
3. Agents analyze the impact against **constraints**: actor availability, location windows,
   scene dependencies, daylight, props, continuity
4. Agents create **proposals** with full reasoning: WHY, EVIDENCE, EXPECTED BENEFIT, RISKS, CONFIDENCE
5. A human reviews and **APPROVE / REJECT / EXPLAIN**
6. Only after human approval does the schedule actually change
7. At end of day: a **wrap report** calculated from actual state

---

## Multi-Agent Architecture

| Agent | Responsibility |
|-------|----------------|
| `PRODUCTION_ORCHESTRATOR` | Coordinates all agents, routes production events |
| `SCRIPT_BREAKDOWN_AGENT` | Parses production package into typed domain model |
| `SCHEDULE_AGENT` | Detects actor/location conflicts, creates rescheduling proposals |
| `COVERAGE_AGENT` | Tracks planned vs completed shots, alerts on missing coverage |
| `CONTINUITY_AGENT` | Detects continuity conflicts between shots and scenes |
| `PRODUCTION_RISK_AGENT` | Aggregates and prioritizes production risks |
| `WRAP_REPORT_AGENT` | Generates end-of-day report from actual state |

All agents communicate with the state layer exclusively through **typed tool calls**.
Agents never access the database directly.

---

## FACT / INFERENCE / RECOMMENDATION / HUMAN_DECISION

These four categories are always kept separate and visually distinct:

| Category | Example |
|----------|---------|
| **FACT** | Maya Reed reported unavailable until 11:30 |
| **INFERENCE** | Scenes 14 and 18 cannot currently be shot |
| **RECOMMENDATION** | Move Scene 22 before Scene 18 |
| **HUMAN_DECISION** | Approved by Production Manager at 10:14 |

---

## Google Cloud Architecture

| Service | Purpose |
|---------|---------|
| **Gemini** | LLM inference for all agents *(Phase 2)* |
| **Agent Builder** | Official Google agent runtime / orchestration *(Phase 2)* |
| **Cloud Run** | FastAPI tool server + Next.js frontend |
| **Firestore** | Production state storage *(Phase 2)* |
| **Cloud Logging** | Structured audit trail with correlation IDs |
| **Secret Manager** | Partner credentials only |
| **IAM + ADC** | Authentication — no service account key files |

Phase 1 runs fully locally with an in-memory store and deterministic agents.

---

## Human Approval

Human approval is **mandatory** for:
- Schedule changes
- Continuity alert overrides
- CRITICAL / HIGH risk resolution
- Marking scenes COMPLETE with open coverage alerts
- Deleting production data

---

## Security

- Agents never access Firestore directly
- All mutations: schema validation → authorization → approval gate → audit log
- No secrets in code or Git
- Application Default Credentials (ADC), no key files
- See [SECURITY.md](SECURITY.md)

---

## Local Development (Phase 1)

No Google Cloud account required for Phase 1.

**Backend:**
```bash
cd services/api
pip install -e ".[dev]"
uvicorn main:app --reload
```

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

**Run tests:**
```bash
# Backend
cd services/api && pytest

# Frontend
cd apps/web && npm test

# Lint + typecheck
cd apps/web && npm run lint && npm run typecheck
```

---

## Environment Variables

Copy `.env.example` to `.env.local`. No secrets needed for Phase 1.

See [.env.example](.env.example) for full reference.

---

## IBM Bob Usage

This project is built using **IBM Bob** as the development AI assistant.

All development actions are logged in real time:
[docs/IBM_BOB_DEVELOPMENT_LOG.md](docs/IBM_BOB_DEVELOPMENT_LOG.md)

---

## Partner Integration

**Status: `NOT_CONFIGURED`**

Partner integration will be implemented only after official contest partner runtime
requirements are confirmed. No fake connections are claimed.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the `PartnerIntegrationPort` design.

---

## Demo Film — LAST LIGHT

A fully **original, synthetic** production package for a fictional short film.

- 4 fictional actors
- 3 fictional locations
- 10 scenes, 22+ planned shots
- Built-in continuity conflict for demo
- Actor delay demo scenario

All names, characters, locations, and props are invented. No real IP used.

---

## Cloud Deployment (Phase 2)

Requires Google Cloud project with billing enabled.
See `PHASE_2_REQUIRED_USER_ACTIONS` in the milestone report.

---

## Contest Compliance

- Real Gemini + Agent Builder: Phase 2 (before submission)
- IBM Bob development evidence: [docs/IBM_BOB_DEVELOPMENT_LOG.md](docs/IBM_BOB_DEVELOPMENT_LOG.md)
- No third-party AI models (OpenAI, Anthropic, etc.)
- No secrets in Git
- Human approval gates enforced in code
- Partner integration: NOT_CONFIGURED until requirements confirmed

## Known Limitations (Phase 1)

- AI not connected (`DEV MODE — AI NOT CONNECTED` shown in UI)
- Firestore not connected (in-memory store)
- Partner integration not configured
- Single production (LAST LIGHT) only
- No Cloud Run deployment yet
