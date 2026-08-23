from __future__ import annotations

import pytest

from services.api.command_router import (
    CommandRoutingError,
    ProductionCommandRouter,
)


class _Response:
    def __init__(self, *, text: str | None = None, parsed=None) -> None:
        self.text = text
        self.parsed = parsed


class _Models:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        return self.response


class _Client:
    def __init__(self, response: _Response) -> None:
        self.models = _Models(response)


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
