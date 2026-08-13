"""Continuity router."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..domain.enums import FactSource, OriginType, Severity
from ..domain.models import ContinuityFact

router = APIRouter()


class RecordFactRequest(BaseModel):
    sceneId: str
    attribute: str
    value: str
    source: FactSource
    shotId: str | None = None
    characterId: str | None = None
    propId: str | None = None
    callerId: str = "script_supervisor"


class ResolveAlertRequest(BaseModel):
    resolution: str
    resolvedBy: str = "script_supervisor"
    override: bool = False


@router.get("/facts")
async def list_facts(request: Request):
    store = request.app.state.store
    return [f.model_dump() for f in store.continuity_facts.values()]


@router.get("/alerts")
async def list_alerts(request: Request):
    store = request.app.state.store
    return [a.model_dump() for a in store.continuity_alerts.values()]


@router.post("/facts")
async def record_fact(body: RecordFactRequest, request: Request):
    store = request.app.state.store
    registry = request.app.state.registry
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")
    fact = ContinuityFact(
        sceneId=body.sceneId,
        attribute=body.attribute,
        value=body.value,
        source=body.source,
        shotId=body.shotId,
        characterId=body.characterId,
        propId=body.propId,
    )
    result = await registry.record_continuity_fact(
        fact=fact,
        shoot_day_id=day.shootDayId,
        caller_type=OriginType.HUMAN,
        caller_id=body.callerId,
        correlation_id=str(uuid.uuid4()),
    )
    return result.model_dump()


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, body: ResolveAlertRequest, request: Request):
    store = request.app.state.store
    from ..domain.enums import AlertStatus
    alert = store.continuity_alerts.get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    updated = alert.model_copy(update={
        "status": AlertStatus.RESOLVED if not body.override else AlertStatus.OVERRIDDEN,
        "resolution": body.resolution,
        "resolvedBy": body.resolvedBy,
    })
    store.upsert_continuity_alert(updated)
    return updated.model_dump()
