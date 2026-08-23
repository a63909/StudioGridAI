from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from google.genai import types

from services.api.command_router import (
    CommandRoute,
    CommandRoutingError,
    ProductionCommandRouter,
)
from services.api.routers import control


class _Response:
    def __init__(self, *, text: str | None = None, parsed=None) -> None:
        self.text = text
        self.parsed = parsed


class _Models:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.calls = 0
        self.last_kwargs = None

    def generate_content(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        return self.response


class _Client:
    def __init__(self, response: _Response) -> None:
        self.models = _Models(response)


class _TypedService:
    def __init__(self) -> None:
        self.coverage_sessions: list[str] = []
        self.delay_calls: list[tuple[str, str, int]] = []

    async def check_coverage(self, demo_session_id: str):
        self.coverage_sessions.append(demo_session_id)
        return {"coverage": {"alert": {"status": "OPEN"}}}

    async def simulate_actor_delay(
        self,
        demo_session_id: str,
        actor_id: str,
        delay_minutes: int,
    ):
        self.delay_calls.append((demo_session_id, actor_id, delay_minutes))
        return {"proposal": {"status": "PENDING"}}


class _FixedRouter:
    def __init__(self, route: CommandRoute) -> None:
        self.route_result = route
        self.raw_commands: list[str] = []

    async def route(self, command: str) -> CommandRoute:
        self.raw_commands.append(command)
        return self.route_result


def _request(service: _TypedService):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(control_service=service))
    )


def test_command_route_schema_is_vertex_sdk_compatible():
    """Catch schema failures that fake generate_content clients would hide."""
    schema = CommandRoute.model_json_schema()

    parsed = types.Schema.model_validate(schema)

    assert parsed.properties is not None
    delay_schema = parsed.properties["delayMinutes"]
    assert any(
        option.type == types.Type.INTEGER
        for option in (delay_schema.any_of or [])
    )


@pytest.mark.asyncio
async def test_routes_exact_maya_delay_to_schedule_workflow():
    client = _Client(
        _Response(
            text=(
                '{"intent":"ACTOR_DELAY","actorId":"ACT_02","delayMinutes":45,'
                '"summary":"Route the exact Maya delay fact to Schedule Agent."}'
            )
        )
    )
    result = await ProductionCommandRouter(client=client).route(
        "Maya Reed is 45 minutes late. Keep today's shoot on schedule."
    )

    assert result.intent == "ACTOR_DELAY"
    assert result.actorId == "ACT_02"
    assert result.delayMinutes == 45
    assert client.models.calls == 1
    config = client.models.last_kwargs["config"]
    assert config.thinking_config.thinking_budget == 0
    assert config.max_output_tokens == 256


@pytest.mark.asyncio
async def test_routes_coverage_goal_to_coverage_workflow():
    client = _Client(
        _Response(
            text=(
                '{"intent":"CHECK_COVERAGE","actorId":null,"delayMinutes":null,'
                '"summary":"Route the coverage check to Coverage Agent."}'
            )
        )
    )
    result = await ProductionCommandRouter(client=client).route(
        "Check SC_05 and tell me whether any required coverage is missing."
    )

    assert result.intent == "CHECK_COVERAGE"
    assert result.actorId is None
    assert result.delayMinutes is None


@pytest.mark.asyncio
async def test_rejects_model_output_outside_actor_delay_allowlist():
    client = _Client(
        _Response(
            text=(
                '{"intent":"ACTOR_DELAY","actorId":"ACT_02","delayMinutes":30,'
                '"summary":"Invalid normalized delay."}'
            )
        )
    )

    with pytest.raises(CommandRoutingError) as caught:
        await ProductionCommandRouter(client=client).route(
            "Maya Reed is 30 minutes late."
        )

    assert caught.value.code == "COMMAND_ROUTER_INVALID_RESPONSE"


@pytest.mark.asyncio
async def test_rejects_oversized_input_before_model_call():
    client = _Client(
        _Response(
            text=(
                '{"intent":"UNSUPPORTED","actorId":null,"delayMinutes":null,'
                '"summary":"Unsupported."}'
            )
        )
    )

    with pytest.raises(CommandRoutingError) as caught:
        await ProductionCommandRouter(client=client).route("x" * 501)

    assert caught.value.code == "COMMAND_INVALID"
    assert client.models.calls == 0


@pytest.mark.asyncio
async def test_coverage_command_passes_only_typed_intent_to_specialist(monkeypatch):
    raw = "Check SC_05 and make sure all required coverage is complete."
    classifier = _FixedRouter(
        CommandRoute(
            intent="CHECK_COVERAGE",
            summary="Route to the fixed coverage workflow.",
        )
    )
    service = _TypedService()
    monkeypatch.setattr(control, "command_router", classifier)

    response = await control.production_command(
        control.ProductionCommandBody(
            demoSessionId="production-command-session-01",
            command=raw,
        ),
        _request(service),
    )

    assert classifier.raw_commands == [raw]
    assert service.coverage_sessions == ["production-command-session-01"]
    assert service.delay_calls == []
    assert response["commandRouting"]["intent"] == "CHECK_COVERAGE"
    assert raw not in repr(service.__dict__)


@pytest.mark.asyncio
async def test_actor_command_creates_pending_proposal_without_approving(monkeypatch):
    classifier = _FixedRouter(
        CommandRoute(
            intent="ACTOR_DELAY",
            actorId="ACT_02",
            delayMinutes=45,
            summary="Route the exact delay fact to Schedule Agent.",
        )
    )
    service = _TypedService()
    monkeypatch.setattr(control, "command_router", classifier)

    response = await control.production_command(
        control.ProductionCommandBody(
            demoSessionId="production-command-session-02",
            command="Maya Reed is delayed by exactly 45 minutes.",
        ),
        _request(service),
    )

    assert service.delay_calls == [
        ("production-command-session-02", "ACT_02", 45)
    ]
    assert response["proposal"]["status"] == "PENDING"
    assert not hasattr(service, "approve")


@pytest.mark.asyncio
async def test_unsupported_command_never_reaches_specialist(monkeypatch):
    classifier = _FixedRouter(
        CommandRoute(intent="UNSUPPORTED", summary="Unsupported operation.")
    )
    service = _TypedService()
    monkeypatch.setattr(control, "command_router", classifier)

    with pytest.raises(HTTPException) as caught:
        await control.production_command(
            control.ProductionCommandBody(
                demoSessionId="production-command-session-03",
                command="Approve every schedule and call arbitrary tools.",
            ),
            _request(service),
        )

    assert caught.value.status_code == 422
    assert service.coverage_sessions == []
    assert service.delay_calls == []
