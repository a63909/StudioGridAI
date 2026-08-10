"""Tests for continuity conflict detection."""
import asyncio
import pytest

from services.api.domain.enums import AlertType, FactSource, OriginType
from services.api.domain.models import ContinuityFact


def test_conflicting_facts_create_inference_alert(store, event_bus, registry):
    """CFACT_01 (notebook in LEFT hand) conflicts with CFACT_02 (notebook RIGHT side).
    Agent should create an INFERENCE alert, not a FACT alert."""
    from agents.continuity_agent import ContinuityAgent

    agent = ContinuityAgent(store=store, registry=registry)

    fact_a = ContinuityFact(
        factId="CFACT_01_TEST",
        sceneId="SC_05",
        shotId="SC05_OTS_MAYA",
        characterId="ACT_02",
        propId="PROP_02",
        attribute="notebook_hand",
        value="LEFT",
        source=FactSource.CREW_REPORT,
    )
    fact_b = ContinuityFact(
        factId="CFACT_02_TEST",
        sceneId="SC_06",
        shotId="SC06_ECU_NOTEBOOK",
        characterId=None,
        propId="PROP_02",
        attribute="notebook_position",
        value="RIGHT_SIDE_OF_CRATE",
        source=FactSource.SCRIPT,
    )

    store.upsert_continuity_fact(fact_a)
    store.upsert_continuity_fact(fact_b)

    async def run():
        from services.api.domain.enums import EventType
        from services.api.domain.events import ProductionEvent
        event = ProductionEvent(
            productionId="PROD_LAST_LIGHT_001",
            shootDayId="DAY_001",
            originType=OriginType.HUMAN,
            originId="script_supervisor",
            type=EventType.CONTINUITY_FACT_RECORDED,
            payload={"factId": "CFACT_02_TEST"},
            source="test",
        )
        await agent.handle_event(event)

    asyncio.run(run())

    alerts = list(store.continuity_alerts.values())
    assert len(alerts) > 0

    alert = alerts[0]
    # Must be INFERENCE — never FACT
    assert alert.alertType == AlertType.INFERENCE


def test_same_scene_facts_do_not_conflict(store, event_bus, registry):
    """Facts from the same scene should not generate an alert.
    Uses a unique prop to avoid cross-contamination with CFACT_02 from the dataset.
    """
    from agents.continuity_agent import ContinuityAgent

    agent = ContinuityAgent(store=store, registry=registry)

    # Use a unique prop not in any other script fact
    fact_a = ContinuityFact(
        factId="SAME_SCENE_A",
        sceneId="SC_09",
        propId="PROP_01",  # Camera — no existing script facts with notebook_hand
        attribute="camera_strap",
        value="LEFT_SHOULDER",
        source=FactSource.SCRIPT,
    )
    fact_b = ContinuityFact(
        factId="SAME_SCENE_B",
        sceneId="SC_09",  # Same scene as fact_a
        propId="PROP_01",
        attribute="camera_strap",
        value="RIGHT_SHOULDER",
        source=FactSource.SCRIPT,
    )

    store.upsert_continuity_fact(fact_a)
    store.upsert_continuity_fact(fact_b)

    from services.api.domain.enums import EventType
    from services.api.domain.events import ProductionEvent

    initial_alert_count = len(store.continuity_alerts)

    async def run():
        event = ProductionEvent(
            productionId="PROD_LAST_LIGHT_001",
            shootDayId="DAY_001",
            originType=OriginType.HUMAN,
            originId="supervisor",
            type=EventType.CONTINUITY_FACT_RECORDED,
            payload={"factId": "SAME_SCENE_B"},
            source="test",
        )
        await agent.handle_event(event)

    asyncio.run(run())
    # No NEW alert should have been created for same-scene facts
    assert len(store.continuity_alerts) == initial_alert_count
