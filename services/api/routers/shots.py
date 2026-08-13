"""Shots router."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..core.approval_gates import ApprovalRequiredError
from ..domain.enums import OriginType
from ..domain.models import Shot

router = APIRouter()


class StartShotRequest(BaseModel):
    shootDayId: str
    startedAt: datetime | None = None
    callerId: str = "first_ad"


class CompleteShotRequest(BaseModel):
    shootDayId: str
    completedAt: datetime | None = None
    actualDurationMinutes: int | None = None
    callerId: str = "first_ad"


@router.get("/", response_model=list[Shot])
async def list_shots(request: Request):
    store = request.app.state.store
    return list(store.shots.values())


@router.get("/{shot_id}", response_model=Shot)
async def get_shot(shot_id: str, request: Request):
    store = request.app.state.store
    shot = store.shots.get(shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail=f"Shot {shot_id} not found")
    return shot


@router.post("/{shot_id}/start")
async def start_shot(shot_id: str, body: StartShotRequest, request: Request):
    store = request.app.state.store
    registry = request.app.state.registry
    import uuid
    try:
        shot = await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id=body.callerId,
            correlation_id=str(uuid.uuid4()),
            started_at=body.startedAt,
        )
        return shot.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{shot_id}/complete")
async def complete_shot(shot_id: str, body: CompleteShotRequest, request: Request):
    store = request.app.state.store
    registry = request.app.state.registry
    import uuid
    try:
        shot = await registry.record_shot_completed(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id=body.callerId,
            correlation_id=str(uuid.uuid4()),
            completed_at=body.completedAt,
            actual_duration_minutes=body.actualDurationMinutes,
        )
        return shot.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
