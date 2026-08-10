"""Production router — dashboard stats and production state."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..domain.enums import AgentMode, PartnerIntegrationStatus
from ..domain.models import DashboardStats

router = APIRouter()


@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request):
    """Get current dashboard statistics calculated from actual state."""
    store = request.app.state.store
    day = store.get_active_shoot_day()
    shoot_day_id = day.shootDayId if day else "DAY_001"
    return store.compute_dashboard_stats(shoot_day_id)


@router.get("/state")
async def get_production_state(request: Request):
    """Get full production state."""
    store = request.app.state.store
    if store.production is None:
        return {"error": "No production loaded"}
    return {
        "production": store.production.model_dump(),
        "actors": {k: v.model_dump() for k, v in store.actors.items()},
        "locations": {k: v.model_dump() for k, v in store.locations.items()},
        "props": {k: v.model_dump() for k, v in store.props.items()},
        "agentMode": AgentMode.DEV,
        "partnerStatus": PartnerIntegrationStatus.NOT_CONFIGURED,
    }
