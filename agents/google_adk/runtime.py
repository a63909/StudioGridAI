"""Shared Google ADK runtime configuration and safe execution traces.

The model endpoint and the managed agent runtime use different locations:
Gemini 3.6 Flash is served from ``global`` while Agent Engine is prepared for
``europe-west3``. Authentication is Application Default Credentials only.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from services.api.config import settings
from services.api.domain.enums import AgentMode
from services.api.domain.models import AgentExecution, ToolCall

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.6-flash"
MODEL_LOCATION = "global"
AGENT_ENGINE_LOCATION = "europe-west3"

_runtime_status = "NOT_CONNECTED"
_gemini_status = "NOT_CONNECTED"
_last_successful_execution_id: str | None = None
_last_model_name: str | None = None
_connection_error_code: str | None = None


class RuntimeConfigurationError(RuntimeError):
    """Raised when runtime settings would silently substitute the verified model."""


def configure_vertex_ai() -> None:
    """Configure ADK to use Vertex AI with ADC and the verified global model endpoint."""
    if settings.GEMINI_MODEL != MODEL_NAME:
        raise RuntimeConfigurationError(
            f"MODEL_BLOCKER: expected {MODEL_NAME}, configured {settings.GEMINI_MODEL}"
        )
    if settings.GOOGLE_CLOUD_LOCATION != MODEL_LOCATION:
        raise RuntimeConfigurationError(
            f"MODEL_BLOCKER: {MODEL_NAME} requires location {MODEL_LOCATION}, "
            f"configured {settings.GOOGLE_CLOUD_LOCATION}"
        )

    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.GOOGLE_CLOUD_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.GOOGLE_CLOUD_LOCATION
    os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = settings.GOOGLE_CLOUD_PROJECT
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    logger.info(
        "vertex_ai_configured",
        extra={
            "project": settings.GOOGLE_CLOUD_PROJECT,
            "modelLocation": settings.GOOGLE_CLOUD_LOCATION,
            "agentEngineLocation": settings.GOOGLE_CLOUD_AGENT_ENGINE_LOCATION,
            "model": MODEL_NAME,
        },
    )


def get_runtime_status() -> dict[str, Any]:
    """Return public operational status; never model reasoning or credentials."""
    return {
        "adkRuntime": _runtime_status,
        "geminiStatus": _gemini_status,
        "lastExecutionId": _last_successful_execution_id,
        "modelName": _last_model_name or MODEL_NAME,
        "connectionErrorCode": _connection_error_code,
        "modelLocation": MODEL_LOCATION,
        "agentEngineLocation": AGENT_ENGINE_LOCATION,
    }


def mark_runtime_success(execution_id: str, model_name: str) -> None:
    global _runtime_status, _gemini_status
    global _last_successful_execution_id, _last_model_name, _connection_error_code
    _runtime_status = "CONNECTED"
    _gemini_status = "CONNECTED"
    _last_successful_execution_id = execution_id
    _last_model_name = model_name
    _connection_error_code = None


def mark_runtime_error(error_code: str) -> None:
    global _runtime_status, _gemini_status, _connection_error_code
    _runtime_status = "ERROR"
    _gemini_status = "ERROR"
    _connection_error_code = error_code


def reset_runtime_status() -> None:
    global _runtime_status, _gemini_status
    global _last_successful_execution_id, _last_model_name, _connection_error_code
    _runtime_status = "NOT_CONNECTED"
    _gemini_status = "NOT_CONNECTED"
    _last_successful_execution_id = None
    _last_model_name = None
    _connection_error_code = None


def build_execution_trace(
    *,
    execution_id: str,
    agent_name: str,
    model_name: str,
    event_id: str,
    correlation_id: str,
    started_at: datetime,
    completed_at: datetime,
    tool_calls: list[ToolCall],
    status: str,
    evidence_references: list[str],
    short_rationale: str,
    error_code: str | None = None,
) -> AgentExecution:
    """Build an operational trace with no private chain-of-thought."""
    duration_ms = max(0, int((completed_at - started_at).total_seconds() * 1000))
    return AgentExecution(
        executionId=execution_id,
        correlationId=correlation_id,
        agentName=agent_name,
        modelName=model_name,
        eventId=event_id,
        startedAt=started_at,
        completedAt=completed_at,
        durationMs=duration_ms,
        toolCalls=tool_calls,
        status=status,
        errorCode=error_code,
        evidenceReferences=evidence_references,
        shortRationale=short_rationale,
        mode=AgentMode.PRODUCTION,
    )
