"""FastAPI Tool Server endpoints exposed to the Google ADK runtime.

Only create-proposal, create-coverage-alert, and safe trace persistence are
available to agents. Human approval endpoints are deliberately absent.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from agents.google_adk.runtime import MODEL_NAME

from ..core.tool_registry import ToolAuthorizationError
from ..domain.enums import OriginType
from ..domain.models import CoverageAlert, ScheduleProposal
from ..tools.contracts import (
    AgentCreateCoverageAlertRequest,
    AgentCreateScheduleProposalRequest,
    AgentExecutionRequest,
)

router = APIRouter()


def _require_agent(actual: str, expected: str) -> None:
    if actual != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tool is restricted to {expected}",
        )


@router.post("/agent/schedule-proposals")
async def create_agent_schedule_proposal(
    body: AgentCreateScheduleProposalRequest, request: Request
):
    _require_agent(body.callerId, "SCHEDULE_AGENT")
    registry = request.app.state.registry
    proposal = ScheduleProposal(
        **body.input.model_dump(exclude={"originAgent"}),
        originAgent=body.callerId,
        agentExecutionId=body.executionId,
        correlationId=body.correlationId,
        modelName=MODEL_NAME,
    )
    try:
        result = await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id=body.input.shootDayId,
            caller_type=OriginType.AGENT,
            caller_id=body.callerId,
            correlation_id=body.correlationId,
        )
    except ToolAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.post("/agent/coverage-alerts")
async def create_agent_coverage_alert(
    body: AgentCreateCoverageAlertRequest, request: Request
):
    _require_agent(body.callerId, "COVERAGE_AGENT")
    registry = request.app.state.registry
    alert = CoverageAlert(**body.input.model_dump())
    try:
        result = await registry.create_coverage_alert(
            alert=alert,
            shoot_day_id=body.shootDayId,
            caller_type=OriginType.AGENT,
            caller_id=body.callerId,
            correlation_id=body.correlationId,
        )
    except ToolAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.post("/agent/executions")
async def record_agent_execution(body: AgentExecutionRequest, request: Request):
    if body.callerId not in {"SCHEDULE_AGENT", "COVERAGE_AGENT"}:
        raise HTTPException(status_code=403, detail="Unknown agent trace caller")
    try:
        result = await request.app.state.registry.record_agent_execution(
            execution=body.execution,
            caller_type=OriginType.AGENT,
            caller_id=body.callerId,
            correlation_id=body.correlationId,
        )
    except (ToolAuthorizationError, ValueError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return result.model_dump(mode="json")
