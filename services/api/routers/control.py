"""IAM-private HTTP surface for predefined LAST LIGHT demo operations."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator

from ..control_service import ControlPlaneError, DemoControlService

router = APIRouter()

SESSION_PATTERN = r"^[A-Za-z0-9_-]{16,80}$"
RESOURCE_ID_PATTERN = r"^[A-Za-z0-9_-]{8,80}$"


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
