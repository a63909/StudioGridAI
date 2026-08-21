# ADR 002 — Agent Interfaces and AI Boundary

**Status:** Accepted
**Date:** August 2026
**Milestone:** STUDIOGRID_AI_PRODUCTION_CONTROL_MVP_1

## Context

Phase 1 must establish clean interfaces so that real Gemini / Google Cloud Agent Builder
can be plugged in during Phase 2 without rewriting business logic or tool contracts.

The contest requires real Gemini + Agent Builder integration before submission.
Phase 1 must not risk becoming a "deterministic simulator without AI" if Phase 2
is delayed.

## Decision

1. All agents implement `BaseAgent` abstract interface
2. Agents communicate with the state layer **exclusively** through typed tool calls
3. Tool calls pass through: schema validation → authorization → approval gate → audit log
4. Phase 1 agents are deterministic implementations behind the same interface
5. `AgentMode` enum distinguishes `DEV` (Phase 1) from `PRODUCTION` (Phase 2)
6. UI always shows current mode honestly (`DEV MODE — AI NOT CONNECTED` banner)
7. `AgentBuilderAdapter` is a placeholder in Phase 1 with a `NotImplementedError`
8. Phase 2 implementation must verify **current** official Agent Builder SDK before coding

## Consequences

### Positive
- Phase 2 replaces agent internals without changing tool contracts
- Tests cover tool contracts and state mutations, not model prose
- No fake AI presented as real in any phase
- Clean separation of concerns

### Negative
- Slightly more abstraction than a single-file implementation
- Phase 2 requires verifying current SDK (Agent Builder API changes frequently)

## AI Mode Transparency

The UI banner `DEV MODE — AI NOT CONNECTED` is visible on every page in Phase 1.
It will be replaced with `PRODUCTION — Gemini` only when real inference is active.

## Alternatives Considered

- Build entire UI first, connect AI later: rejected (risk of no AI at submission)
- Use OpenAI/Anthropic for development: explicitly prohibited by contest rules
