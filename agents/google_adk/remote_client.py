"""Server-side client for the fixed StudioGrid Vertex AI Agent Engine.

The client deliberately returns only operational metadata. Remote prompts,
production context, credentials, and model reasoning never cross this boundary.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from services.api.config import settings

from .cloud_agent import (
    build_coverage_session_state,
    build_remote_message,
    build_schedule_session_state,
)
from .runtime import AGENT_ENGINE_LOCATION


class RemoteAgentEngineError(RuntimeError):
    """A redacted failure at the managed Agent Engine boundary."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class RemoteInvocation:
    session_id: str
    execution_id: str
    route: str
    tool_attempted: bool
    proposal_created: bool
    alert_created: bool
    last_result: dict[str, Any]
    last_error_code: str | None
    events: list[dict[str, Any]]


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _session_id(session: Any) -> str:
    payload = _jsonable(session)
    if isinstance(payload, dict):
        for key in ("id", "session_id", "sessionId"):
            if payload.get(key):
                return str(payload[key])
        if payload.get("name"):
            return str(payload["name"]).rsplit("/", 1)[-1]
    raise RemoteAgentEngineError("AGENT_SESSION_ID_MISSING")


def _safe_state(session: Any) -> dict[str, Any]:
    payload = _jsonable(session)
    state = payload.get("state") if isinstance(payload, dict) else None
    if not isinstance(state, dict):
        raise RemoteAgentEngineError("AGENT_SESSION_STATE_MISSING")
    result = state.get("lastResult")
    return {
        "route": state.get("route"),
        "executionId": state.get("executionId"),
        "toolAttempted": state.get("toolAttempted") is True,
        "proposalCreated": state.get("proposalCreated") is True,
        "alertCreated": state.get("alertCreated") is True,
        "lastResult": result if isinstance(result, dict) else {},
        "lastErrorCode": state.get("lastErrorCode"),
    }


def _safe_event(event: Any) -> dict[str, Any]:
    payload = _jsonable(event)
    if not isinstance(payload, dict):
        return {"eventType": type(event).__name__}
    summary: dict[str, Any] = {}
    for key in ("id", "author", "invocation_id", "branch"):
        if payload.get(key) is not None:
            summary[key] = payload[key]
    calls: list[str] = []
    responses: list[dict[str, Any]] = []
    content = payload.get("content")
    parts = content.get("parts", []) if isinstance(content, dict) else []
    for part in parts:
        if not isinstance(part, dict):
            continue
        call = part.get("function_call") or part.get("functionCall")
        if isinstance(call, dict) and call.get("name"):
            calls.append(str(call["name"]))
        response = part.get("function_response") or part.get("functionResponse")
        if isinstance(response, dict):
            value = response.get("response")
            safe_value = value if isinstance(value, dict) else {}
            responses.append(
                {
                    "name": response.get("name"),
                    "status": safe_value.get("status"),
                    "proposalId": safe_value.get("proposalId"),
                    "alertId": safe_value.get("alertId"),
                    "errorCode": safe_value.get("errorCode"),
                }
            )
    if calls:
        summary["functionCalls"] = calls
    if responses:
        summary["functionResponses"] = responses
    return summary


class RemoteAgentEngineClient:
    """Invoke only the preconfigured StudioGrid Agent Engine resource."""

    def __init__(self, remote: Any | None = None) -> None:
        self._remote = remote
        self._init_lock = asyncio.Lock()

    async def _get_remote(self) -> Any:
        if self._remote is not None:
            return self._remote
        async with self._init_lock:
            if self._remote is None:
                try:
                    import agentplatform

                    client = agentplatform.Client(
                        project=settings.GOOGLE_CLOUD_PROJECT,
                        location=AGENT_ENGINE_LOCATION,
                    )
                    self._remote = await asyncio.to_thread(
                        client.agent_engines.get,
                        name=settings.STUDIOGRID_AGENT_ENGINE_RESOURCE,
                    )
                except Exception as exc:
                    raise RemoteAgentEngineError(
                        f"AGENT_ENGINE_INIT_{type(exc).__name__.upper()}"
                    ) from exc
        return self._remote

    async def healthcheck(self) -> list[str]:
        """Perform a real resource operation-schema request."""
        try:
            remote = await self._get_remote()
            schemas = await asyncio.to_thread(remote.operation_schemas)
            return sorted(
                str(item.get("name"))
                for item in (schemas or [])
                if isinstance(item, dict) and item.get("name")
            )
        except RemoteAgentEngineError:
            raise
        except Exception as exc:
            raise RemoteAgentEngineError(
                f"AGENT_ENGINE_HEALTH_{type(exc).__name__.upper()}"
            ) from exc

    async def invoke_schedule(self, store: Any, event: Any, demo_session_id: str) -> RemoteInvocation:
        state = build_schedule_session_state(store, event)
        return await self._invoke(state, demo_session_id)

    async def invoke_coverage(self, store: Any, event: Any, demo_session_id: str) -> RemoteInvocation:
        state = build_coverage_session_state(store, event)
        return await self._invoke(state, demo_session_id)

    async def _invoke(self, state: dict[str, Any], demo_session_id: str) -> RemoteInvocation:
        remote = await self._get_remote()
        user_id = f"studiogrid-demo-{demo_session_id}"
        try:
            created = await remote.async_create_session(user_id=user_id, state=state)
            session_id = _session_id(created)
            summaries: list[dict[str, Any]] = []
            async for event in remote.async_stream_query(
                user_id=user_id,
                session_id=session_id,
                message=build_remote_message(state),
            ):
                summaries.append(_safe_event(event))
            fetched = await remote.async_get_session(
                user_id=user_id,
                session_id=session_id,
            )
            safe = _safe_state(fetched)
        except RemoteAgentEngineError:
            raise
        except Exception as exc:
            raise RemoteAgentEngineError(
                f"AGENT_ENGINE_QUERY_{type(exc).__name__.upper()}"
            ) from exc
        execution_id = safe.get("executionId")
        if not execution_id:
            raise RemoteAgentEngineError("AGENT_EXECUTION_ID_MISSING")
        return RemoteInvocation(
            session_id=session_id,
            execution_id=str(execution_id),
            route=str(safe.get("route") or "UNKNOWN"),
            tool_attempted=safe["toolAttempted"],
            proposal_created=safe["proposalCreated"],
            alert_created=safe["alertCreated"],
            last_result=safe["lastResult"],
            last_error_code=(
                str(safe["lastErrorCode"]) if safe.get("lastErrorCode") else None
            ),
            events=summaries,
        )
