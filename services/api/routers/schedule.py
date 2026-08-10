"""Schedule router — schedule management, proposals, approval."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..core.approval_gates import ApprovalRequiredError
from ..core.tool_registry import ToolRegistry
from ..domain.enums import OriginType, ProposalCategory, Severity
from ..domain.models import Evidence, ProposalRisk, ScheduleChange, ScheduleProposal

router = APIRouter()


class ActorDelayRequest(BaseModel):
    actorId: str
    delayMinutes: int
    reason: str
    callerId: str = "production_manager"


class ActorAvailableRequest(BaseModel):
    actorId: str
    callerId: str = "production_manager"


class ApproveProposalRequest(BaseModel):
    approvedBy: str = "production_manager"


class RejectProposalRequest(BaseModel):
    rejectedBy: str = "production_manager"
    reason: str


@router.get("/")
async def get_schedule(request: Request):
    store = request.app.state.store
    day = store.get_active_shoot_day()
    if day is None:
        return {"scheduledScenes": [], "shootDayId": None}
    return {
        "shootDayId": day.shootDayId,
        "date": day.date,
        "status": day.status,
        "scheduledScenes": [s.model_dump() for s in day.scheduledScenes],
    }


@router.get("/proposals")
async def get_proposals(request: Request):
    store = request.app.state.store
    return [p.model_dump() for p in store.proposals.values()]


@router.post("/actor-delay")
async def report_actor_delay(body: ActorDelayRequest, request: Request):
    store = request.app.state.store
    event_bus = request.app.state.event_bus
    registry = ToolRegistry(store=store, event_bus=event_bus)
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")
    try:
        actor = await registry.report_actor_delay(
            actor_id=body.actorId,
            delay_minutes=body.delayMinutes,
            reason=body.reason,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.HUMAN,
            caller_id=body.callerId,
            correlation_id=str(uuid.uuid4()),
        )
        return actor.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/actor-available")
async def report_actor_available(body: ActorAvailableRequest, request: Request):
    store = request.app.state.store
    event_bus = request.app.state.event_bus
    registry = ToolRegistry(store=store, event_bus=event_bus)
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")
    try:
        actor = await registry.report_actor_available(
            actor_id=body.actorId,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.HUMAN,
            caller_id=body.callerId,
            correlation_id=str(uuid.uuid4()),
        )
        return actor.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, body: ApproveProposalRequest, request: Request):
    store = request.app.state.store
    event_bus = request.app.state.event_bus
    registry = ToolRegistry(store=store, event_bus=event_bus)
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")
    try:
        proposal = await registry.approve_schedule_proposal(
            proposal_id=proposal_id,
            approved_by=body.approvedBy,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.HUMAN,
            caller_id=body.approvedBy,
            correlation_id=str(uuid.uuid4()),
        )
        return proposal.model_dump()
    except (ValueError, ApprovalRequiredError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, body: RejectProposalRequest, request: Request):
    store = request.app.state.store
    event_bus = request.app.state.event_bus
    registry = ToolRegistry(store=store, event_bus=event_bus)
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")
    try:
        proposal = await registry.reject_schedule_proposal(
            proposal_id=proposal_id,
            rejected_by=body.rejectedBy,
            reason=body.reason,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.HUMAN,
            caller_id=body.rejectedBy,
            correlation_id=str(uuid.uuid4()),
        )
        return proposal.model_dump()
    except (ValueError, ApprovalRequiredError) as e:
        raise HTTPException(status_code=400, detail=str(e))
