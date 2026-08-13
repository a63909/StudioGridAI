"""Typed client for the FastAPI Tool Server used by Google ADK agents."""
from __future__ import annotations

from typing import Protocol

import httpx

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
    """HTTP implementation used by the real ADK runtime."""

    def __init__(self, base_url: str, timeout_seconds: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def _post(self, path: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._base_url}{path}", json=payload)
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
