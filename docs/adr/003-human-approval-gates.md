# ADR 003 — Human Approval Gates

**Status:** Accepted
**Date:** August 2026
**Milestone:** STUDIOGRID_AI_PRODUCTION_CONTROL_MVP_1

## Context

AI agents must never silently modify production state. Film production errors caused
by automated systems are costly and potentially catastrophic for the shooting schedule.
A rescheduled scene without human awareness could send the entire crew to the wrong
location.

## Decision

Human approval is mandatory for the following operations:

| Operation | Tool | Reason |
|-----------|------|--------|
| Schedule change | `approve_schedule_proposal` | Crew logistics, irreversible |
| Continuity alert override | `resolve_continuity_alert` (override) | Could cause editing problems |
| CRITICAL/HIGH risk resolution | `resolve_risk` | High stakes, requires judgment |
| Scene marked COMPLETE with open coverage alerts | scene status override | Editing risk |
| Deleting production data | any delete tool | Irreversible |
| Wrapping the shoot day | `wrap_shoot_day` | Final, triggers report |

### Implementation

- `ApprovalGate` class wraps each protected tool
- If `caller_type != OriginType.HUMAN` and tool is in `PROTECTED_TOOLS`: raise `ApprovalRequiredError`
- Approval status recorded in audit log with approver identity
- UI shows APPROVE / REJECT / EXPLAIN buttons for each proposal
- Approval confirmation dialog prevents accidental clicks

### What Agents CAN Do Without Human Approval

- Create proposals (cannot approve their own proposals)
- Create alerts (coverage, continuity, risk)
- Record facts (continuity facts, shot events)
- Generate the wrap report (read-only calculation)

## Consequences

### Positive
- AI cannot cause production chaos silently
- All schedule changes are human-confirmed and auditable
- Clear responsibility: human owns the decision

### Negative
- Requires human attention for every schedule change
- Demo must include human interaction to show the workflow

## Alternatives Considered

- Auto-approve low-confidence proposals: rejected (any schedule change affects crew)
- Approve by timeout (if no rejection within N minutes): rejected (implicit consent is not consent)
