"""Typed client for the FastAPI Tool Server used by Google ADK agents."""
from __future__ import annotations

import asyncio
from typing import Protocol

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token

from ..core.tool_registry import ToolRegistry
from ..domain.enums import OriginType
from ..domain.models import AgentExecution, CoverageAlert, ScheduleProposal
from .contracts import CreateCoverageAlertInput, CreateScheduleProposalInput


class ToolServerError(RuntimeError):
    """A typed tool was rejected or unavailable at the FastAPI boundary."""


class AgentToolGateway(Protocol):
    async def create_schedule_proposal(
        self,
        input_data: CreateScheduleProposalInput,
        *,
        caller_id: str,
        correlation_id: str,
        execution_id: str,
    ) -> ScheduleProposal: ...

    async def create_coverage_alert(
        self,
        input_data: CreateCoverageAlertInput,
        *,
        caller_id: str,
        correlation_id: str,
        shoot_day_id: str,
    ) -> CoverageAlert: ...

    async def record_agent_execution(
        self,
        execution: AgentExecution,
        *,
        caller_id: str,
        correlation_id: str,
    ) -> AgentExecution: ...


class FastAPIToolGateway:
    """HTTP gateway with optional Google-signed Cloud Run ID-token auth."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 30.0,
        *,
        authenticated: bool = False,
        audience: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._authenticated = authenticated
        self._audience = (audience or self._base_url).rstrip("/")
        if authenticated and not self._base_url.startswith("https://"):
            raise ValueError("Authenticated Tool Server URL must use HTTPS")

    def _build_auth_headers(self) -> dict[str, str]:
        """Fetch an ephemeral ID token from ADC/runtime identity; never log it."""
        if not self._authenticated:
            return {}
        token = id_token.fetch_id_token(GoogleAuthRequest(), self._audience)
        return {"Authorization": f"Bearer {token}"}

    async def _post(self, path: str, payload: dict) -> dict:
        try:
            headers = await asyncio.to_thread(self._build_auth_headers)
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}{path}",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise ToolServerError(f"Tool Server unavailable: {type(exc).__name__}") from exc
        if not response.is_success:
            raise ToolServerError(
                f"Tool Server rejected {path}: HTTP {response.status_code} {response.text[:300]}"
            )
        return response.json()

    async def create_schedule_proposal(
        self,
        input_data: CreateScheduleProposalInput,
        *,
        caller_id: str,
        correlation_id: str,
        execution_id: str,
    ) -> ScheduleProposal:
        data = await self._post(
            "/tools/agent/schedule-proposals",
            {
                "callerId": caller_id,
                "correlationId": correlation_id,
                "executionId": execution_id,
                "input": input_data.model_dump(mode="json"),
            },
        )
        return ScheduleProposal.model_validate(data)

    async def create_coverage_alert(
        self,
        input_data: CreateCoverageAlertInput,
        *,
        caller_id: str,
        correlation_id: str,
        shoot_day_id: str,
    ) -> CoverageAlert:
        data = await self._post(
            "/tools/agent/coverage-alerts",
            {
                "callerId": caller_id,
                "correlationId": correlation_id,
                "shootDayId": shoot_day_id,
                "input": input_data.model_dump(mode="json"),
            },
        )
        return CoverageAlert.model_validate(data)

    async def record_agent_execution(
        self,
        execution: AgentExecution,
        *,
        caller_id: str,
        correlation_id: str,
    ) -> AgentExecution:
        data = await self._post(
            "/tools/agent/executions",
            {
                "callerId": caller_id,
                "correlationId": correlation_id,
                "execution": execution.model_dump(mode="json"),
            },
        )
        return AgentExecution.model_validate(data)


class DirectToolGateway:
    """In-process gateway for unit tests; production uses ``FastAPIToolGateway``."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def create_schedule_proposal(
        self,
        input_data: CreateScheduleProposalInput,
        *,
        caller_id: str,
        correlation_id: str,
        execution_id: str,
    ) -> ScheduleProposal:
        proposal = ScheduleProposal(
            **input_data.model_dump(),
            originAgent=caller_id,
            agentExecutionId=execution_id,
            correlationId=correlation_id,
        )
        return await self._registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id=input_data.shootDayId,
            caller_type=OriginType.AGENT,
            caller_id=caller_id,
            correlation_id=correlation_id,
        )

    async def create_coverage_alert(
        self,
        input_data: CreateCoverageAlertInput,
        *,
        caller_id: str,
        correlation_id: str,
        shoot_day_id: str,
    ) -> CoverageAlert:
        alert = CoverageAlert(**input_data.model_dump())
        return await self._registry.create_coverage_alert(
            alert=alert,
            shoot_day_id=shoot_day_id,
            caller_type=OriginType.AGENT,
            caller_id=caller_id,
            correlation_id=correlation_id,
        )

    async def record_agent_execution(
        self,
        execution: AgentExecution,
        *,
        caller_id: str,
        correlation_id: str,
    ) -> AgentExecution:
        return await self._registry.record_agent_execution(
            execution=execution,
            caller_type=OriginType.AGENT,
            caller_id=caller_id,
            correlation_id=correlation_id,
        )
