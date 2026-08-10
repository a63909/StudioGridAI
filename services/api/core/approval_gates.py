"""Human Approval Gates for StudioGrid AI.

All state mutations that could cause significant production impact require
explicit human approval. Agents cannot approve their own proposals.
"""
from __future__ import annotations

from ..domain.enums import OriginType, Severity


class ApprovalRequiredError(Exception):
    """Raised when a protected tool is called without human approval."""

    def __init__(self, tool_name: str, reason: str) -> None:
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Human approval required for '{tool_name}': {reason}")


class ApprovalGate:
    """Enforces human approval for protected operations.

    Rules:
    - HUMAN callers always pass (they are the approval)
    - AGENT or SYSTEM callers are blocked for protected tools
    - HIGH/CRITICAL risk resolution has special handling (severity-dependent)
    """

    # Tools that require the caller to be HUMAN
    HUMAN_ONLY_TOOLS: dict[str, str] = {
        "approve_schedule_proposal": (
            "Schedule changes affect the entire crew and cannot be auto-approved by agents."
        ),
        "reject_schedule_proposal": (
            "Schedule proposal rejection is a human decision."
        ),
        "wrap_shoot_day": (
            "Wrapping a shoot day is a final, irreversible action requiring human confirmation."
        ),
        "delete_production_data": (
            "Production data deletion is irreversible and requires human authorization."
        ),
    }

    # Tools where HIGH or CRITICAL severity requires human approval
    SEVERITY_GATED_TOOLS: dict[str, set[Severity]] = {
        "resolve_risk": {Severity.HIGH, Severity.CRITICAL},
        "resolve_continuity_alert": {Severity.HIGH, Severity.CRITICAL},
    }

    @classmethod
    def check(
        cls,
        tool_name: str,
        caller_type: OriginType,
        severity: Severity | None = None,
    ) -> None:
        """Check if this tool call is permitted.

        Args:
            tool_name: The name of the tool being called.
            caller_type: Who is making the call (HUMAN, AGENT, SYSTEM).
            severity: For severity-gated tools, the severity of the affected entity.

        Raises:
            ApprovalRequiredError: If the call is not permitted.
        """
        # Human callers always pass
        if caller_type == OriginType.HUMAN:
            return

        # Check human-only tools
        if tool_name in cls.HUMAN_ONLY_TOOLS:
            raise ApprovalRequiredError(tool_name, cls.HUMAN_ONLY_TOOLS[tool_name])

        # Check severity-gated tools
        if tool_name in cls.SEVERITY_GATED_TOOLS and severity is not None:
            blocked_severities = cls.SEVERITY_GATED_TOOLS[tool_name]
            if severity in blocked_severities:
                raise ApprovalRequiredError(
                    tool_name,
                    f"Resolving a {severity.value} item requires human approval.",
                )
