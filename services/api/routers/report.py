"""Report router — wrap report generation."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..core.approval_gates import ApprovalRequiredError
from ..core.tool_registry import ToolRegistry
from ..domain.enums import EventType, OriginType

router = APIRouter()


class WrapDayRequest(BaseModel):
    wrappedBy: str = "production_manager"


@router.get("/")
async def get_wrap_report(request: Request):
    store = request.app.state.store
    if store.wrap_report is None:
        return {"status": "no_report_yet", "message": "Day has not been wrapped yet."}
    return store.wrap_report.model_dump()


@router.post("/wrap-day")
async def wrap_day(body: WrapDayRequest, request: Request):
    store = request.app.state.store
    event_bus = request.app.state.event_bus
    registry = ToolRegistry(store=store, event_bus=event_bus)
    day = store.get_active_shoot_day()
    if day is None:
        raise HTTPException(status_code=400, detail="No active shoot day")

    from ..domain.events import ProductionEvent
    from ..domain.enums import ShootDayStatus
    corr_id = str(uuid.uuid4())

    # Update shoot day status to WRAPPED
    updated_day = day.model_copy(update={"status": ShootDayStatus.WRAPPED})
    days = list(store.production.shootDays)
    idx = days.index(day)
    days[idx] = updated_day
    store.production = store.production.model_copy(update={"shootDays": days})

    # Publish wrap event (agents will respond)
    event = ProductionEvent(
        productionId=store.production.productionId,
        shootDayId=day.shootDayId,
        originType=OriginType.HUMAN,
        originId=body.wrappedBy,
        type=EventType.SHOOT_DAY_WRAPPED,
        payload={"shootDayId": day.shootDayId, "wrappedBy": body.wrappedBy},
        source=body.wrappedBy,
        correlationId=corr_id,
    )
    store.add_event(event)
    await event_bus.publish(event)

    # Generate report directly too (in case orchestrator not wired in tests)
    report = await registry.generate_wrap_report(
        shoot_day_id=day.shootDayId,
        caller_type=OriginType.HUMAN,
        caller_id=body.wrappedBy,
        correlation_id=corr_id,
    )
    return report.model_dump()
