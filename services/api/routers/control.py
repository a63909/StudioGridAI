"""IAM-private HTTP surface for predefined LAST LIGHT demo operations."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator, model_validator

from agents.google_adk.runtime import MODEL_NAME

from ..command_router import CommandRoutingError, ProductionCommandRouter
from ..control_service import ControlPlaneError, DemoControlService

router = APIRouter()

SESSION_PATTERN = r"^[A-Za-z0-9_-]{16,80}$"
RESOURCE_ID_PATTERN = r"^[A-Za-z0-9_-]{8,80}$"
command_router = ProductionCommandRouter()


class DemoSessionBody(BaseModel):
    demoSessionId: str = Field(pattern=SESSION_PATTERN)
    model_config = {"extra": "forbid"}


class ActorDelayBody(DemoSessionBody):
    actorId: Literal["ACT_02", "ACT_03"]
    delayMinutes: Literal[30, 45]

    @model_validator(mode="after")
    def actor_delay_pair(self):
        expected = {"ACT_02": 45, "ACT_03": 30}
        if expected[self.actorId] != self.delayMinutes:
            raise ValueError("Unsupported actor/delay pairing")
        return self


class ProposalDecisionBody(DemoSessionBody):
    proposalId: str = Field(pattern=RESOURCE_ID_PATTERN)


class ProductionCommandBody(DemoSessionBody):
    command: str = Field(min_length=4, max_length=500)

    @field_validator("command")
    @classmethod
    def normalize_command(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 4 or "\x00" in normalized:
            raise ValueError("Invalid production command")
        return normalized


def _service(request: Request) -> DemoControlService:
    service = getattr(request.app.state, "control_service", None)
    if service is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "CONTROL_API_NOT_READY", "message": "Control API unavailable."},
        )
    return service


async def _run(awaitable):
    try:
        return await awaitable
    except ControlPlaneError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc


@router.get("/health")
async def control_health(request: Request):
    return await _service(request).health()


@router.get("/state")
async def control_state(
    request: Request,
    demoSessionId: str = Query(pattern=SESSION_PATTERN),
):
    return await _run(_service(request).get_state(demoSessionId))


@router.post("/reset")
async def reset_demo(body: DemoSessionBody, request: Request):
    return await _run(_service(request).reset(body.demoSessionId))


@router.post("/command")
async def production_command(body: ProductionCommandBody, request: Request):
    """Route one natural-language goal to an existing typed production workflow."""
    try:
        route = await command_router.route(body.command)
    except CommandRoutingError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": exc.code,
                "message": "Production Command could not be safely interpreted.",
            },
        ) from exc

    if route.intent == "UNSUPPORTED":
        raise HTTPException(
            status_code=422,
            detail={
                "code": "COMMAND_NOT_SUPPORTED",
                "message": (
                    "This demo currently supports exact actor-delay replanning "
                    "and shot-coverage checks."
                ),
            },
        )

    service = _service(request)
    if route.intent == "ACTOR_DELAY":
        if route.actorId is None or route.delayMinutes is None:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "COMMAND_ROUTER_INVALID_RESPONSE",
                    "message": "Production Command returned an incomplete typed route.",
                },
            )
        state = await _run(
            service.simulate_actor_delay(
                body.demoSessionId,
                route.actorId,
                route.delayMinutes,
            )
        )
        target = "SCHEDULE_AGENT"
    else:
        state = await _run(service.check_coverage(body.demoSessionId))
        target = "COVERAGE_AGENT"

    state["commandRouting"] = {
        "provider": "Google Vertex AI",
        "modelName": MODEL_NAME,
        "intent": route.intent,
        "target": target,
        "summary": route.summary,
    }
    return state


@router.post("/actor-delay")
async def actor_delay(body: ActorDelayBody, request: Request):
    return await _run(
        _service(request).simulate_actor_delay(
            body.demoSessionId,
            body.actorId,
            body.delayMinutes,
        )
    )


@router.post("/proposal/approve")
async def approve_proposal(body: ProposalDecisionBody, request: Request):
    return await _run(
        _service(request).approve(body.demoSessionId, body.proposalId)
    )


@router.post("/proposal/reject")
async def reject_proposal(body: ProposalDecisionBody, request: Request):
    return await _run(
        _service(request).reject(body.demoSessionId, body.proposalId)
    )


@router.post("/coverage")
async def coverage_demo(body: DemoSessionBody, request: Request):
    return await _run(_service(request).check_coverage(body.demoSessionId))
