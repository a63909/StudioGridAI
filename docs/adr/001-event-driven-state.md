# ADR 001 — Event-Driven State Management

**Status:** Accepted
**Date:** August 2026
**Milestone:** STUDIOGRID_AI_PRODUCTION_CONTROL_MVP_1

## Context

StudioGrid AI models a real-time shooting day. State changes happen continuously:
shots are completed, actors are delayed, locations become unavailable. Multiple agents
need to react to the same events. The production record must be fully auditable.

## Decision

Adopt an event-driven architecture where:

1. All state changes are triggered by typed `ProductionEvent` objects
2. An `EventBus` dispatches events to subscribers (agents, state manager)
3. Events are immutable once created — never modified, only appended
4. The `EventType` enum defines all valid event types (no free-form strings as event types)
5. Each event carries a `correlationId` for end-to-end tracing
6. Phase 1: `LocalEventBus` (in-process, sync)
7. Phase 2: replaceable with Cloud Pub/Sub without changing agent code

## Consequences

### Positive
- Complete, immutable audit trail of all production day events
- Agents react to events without polling
- Easy replay for testing and demo scenarios
- Decoupled: adding a new agent means subscribing to events, not modifying existing code

### Negative
- Slightly more infrastructure than a simple request/response pattern
- Eventual consistency considerations in Phase 2 (Cloud Pub/Sub)

## Alternatives Considered

- Direct method calls between components: rejected (tight coupling, no audit trail)
- Polling state periodically: rejected (latency, no causality)
