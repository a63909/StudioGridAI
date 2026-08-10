"""Risks router."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..core.approval_gates import ApprovalRequiredError
from ..core.tool_registry import ToolRegistry
from ..domain.enums import OriginType

router = APIRouter()


class ResolveRiskRequest(BaseModel):
    resolvedBy: str = "production_manager"
    resolution: str


@router.get("/")
async def list_risks(request: Request):
    store = request.app.state.store
    return [r.model_dump() for r in store.risks.values()]


@router.post("/{risk_id}/resolve")
async def resolve_risk(risk_id: str, body: ResolveRiskRequest, request: Request):
    store = request.app.state.store
    event_bus = request.app.state.event_bus
    registry = ToolRegistry(store=store, event_bus=event_bus)
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")
    try:
        risk = await registry.resolve_risk(
            risk_id=risk_id,
            resolved_by=body.resolvedBy,
            resolution=body.resolution,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.HUMAN,
            caller_id=body.resolvedBy,
            correlation_id=str(uuid.uuid4()),
        )
        return risk.model_dump()
    except (ValueError, ApprovalRequiredError) as e:
        raise HTTPException(status_code=400, detail=str(e))
