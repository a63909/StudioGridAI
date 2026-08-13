"""Remote StudioGrid Agent Engine smoke with Firestore and session evidence."""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import agentplatform

from agents.google_adk.cloud_agent import (
    build_coverage_session_state,
    build_remote_message,
    build_schedule_session_state,
)
from agents.google_adk.deploy_agent_engine import DISPLAY_NAME, PROJECT_ID
from agents.google_adk.runtime import AGENT_ENGINE_LOCATION, MODEL_NAME
from services.api.db.firestore_store import FirestoreStateStore
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import EventType, OriginType, ShootDayStatus, ShotStatus
from services.api.domain.events import ProductionEvent

USER_ID = "studiogrid-agent-engine-smoke"
PRODUCTION_NAMESPACE = "last-light-demo"


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


def _resource_name(agent: object) -> str:
    api_resource = getattr(agent, "api_resource", None)
    return str(
        getattr(api_resource, "name", None)
        or getattr(agent, "name", None)
        or ""
    )


def _session_id(session: Any) -> str:
    payload = _jsonable(session)
    for key in ("id", "session_id", "sessionId"):
        if isinstance(payload, dict) and payload.get(key):
            return str(payload[key])
    if isinstance(payload, dict) and payload.get("name"):
        return str(payload["name"]).rsplit("/", 1)[-1]
    raise RuntimeError(f"Remote session response has no ID: {payload}")


def _session_state(session: Any) -> dict[str, Any]:
    payload = _jsonable(session)
    if isinstance(payload, dict):
        state = payload.get("state")
        if isinstance(state, dict):
            return state
    raise RuntimeError("Remote session response has no state")


def _safe_session_summaries(value: Any) -> list[dict[str, Any]]:
    """Retain operational state only; never persist session prompts or context."""
    payload = _jsonable(value)
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else payload
    summaries: list[dict[str, Any]] = []
    for item in sessions if isinstance(sessions, list) else []:
        if not isinstance(item, dict):
            continue
        state = item.get("state") if isinstance(item.get("state"), dict) else {}
        summaries.append(
            {
                "sessionId": (
                    item.get("id")
                    or item.get("session_id")
                    or item.get("sessionId")
                    or str(item.get("name", "")).rsplit("/", 1)[-1]
                ),
                "route": state.get("route"),
                "executionId": state.get("executionId"),
                "toolAttempted": state.get("toolAttempted"),
                "proposalCreated": state.get("proposalCreated"),
                "alertCreated": state.get("alertCreated"),
                "lastErrorCode": state.get("lastErrorCode"),
            }
        )
    return summaries


def _safe_invocation_summary(invocation: dict[str, Any]) -> dict[str, Any]:
    """Keep routing/tool proof without persisting prompts or production context."""
    state = invocation["state"]
    return {
        "sessionId": invocation["sessionId"],
        "executionId": state.get("executionId"),
        "route": state.get("route"),
        "toolAttempted": state.get("toolAttempted"),
        "proposalCreated": state.get("proposalCreated"),
        "alertCreated": state.get("alertCreated"),
        "lastErrorCode": state.get("lastErrorCode"),
        "lastResult": state.get("lastResult"),
        "events": invocation["events"],
    }


def _event_summary(event: Any) -> dict[str, Any]:
    payload = _jsonable(event)
    summary: dict[str, Any] = {}
    if not isinstance(payload, dict):
        return {"eventType": type(event).__name__}
    for key in ("id", "author", "invocation_id", "branch"):
        if payload.get(key) is not None:
            summary[key] = payload[key]
    calls: list[str] = []
    responses: list[dict[str, Any]] = []
    content = payload.get("content") or {}
    for part in content.get("parts", []) if isinstance(content, dict) else []:
        call = part.get("function_call") or part.get("functionCall")
        if isinstance(call, dict) and call.get("name"):
            calls.append(str(call["name"]))
        response = part.get("function_response") or part.get("functionResponse")
        if isinstance(response, dict):
            result = response.get("response")
            safe_result = result if isinstance(result, dict) else {}
            responses.append(
                {
                    "name": response.get("name"),
                    "proposalId": safe_result.get("proposalId"),
                    "alertId": safe_result.get("alertId"),
                    "status": safe_result.get("status"),
                    "errorCode": safe_result.get("errorCode"),
                }
            )
    if calls:
        summary["functionCalls"] = calls
    if responses:
        summary["functionResponses"] = responses
    return summary


def _load_store(project_root: Path) -> LocalStateStore:
    package_path = project_root / "demo" / "last_light" / "production_package.json"
    store = LocalStateStore()
    store.load_from_production_package(
        json.loads(package_path.read_text(encoding="utf-8"))
    )
    day = store.get_active_shoot_day()
    if day is None or store.production is None:
        raise RuntimeError("LAST LIGHT has no shoot day")
    active = day.model_copy(update={"status": ShootDayStatus.ACTIVE})
    days = list(store.production.shootDays)
    days[0] = active
    store.production = store.production.model_copy(update={"shootDays": days})
    return store


def _event(
    store: LocalStateStore,
    event_type: EventType,
    payload: dict[str, Any],
    correlation_id: str,
) -> ProductionEvent:
    day = store.get_active_shoot_day()
    assert day is not None and store.production is not None
    return ProductionEvent(
        productionId=store.production.productionId,
        shootDayId=day.shootDayId,
        originType=OriginType.SYSTEM,
        originId="AGENT_ENGINE_SMOKE",
        type=event_type,
        payload=payload,
        source="AGENT_ENGINE_SMOKE",
        correlationId=correlation_id,
    )


def _complete_scene_in_memory(store: LocalStateStore, scene_id: str) -> None:
    """Advance factual smoke context without mutating durable state directly."""
    for shot_id, shot in list(store.shots.items()):
        if shot.sceneId == scene_id:
            store.shots[shot_id] = shot.model_copy(update={"status": ShotStatus.COMPLETE})


async def _invoke(remote: Any, state: dict[str, Any]) -> dict[str, Any]:
    created = await remote.async_create_session(user_id=USER_ID, state=state)
    session_id = _session_id(created)
    summaries: list[dict[str, Any]] = []
    async for event in remote.async_stream_query(
        user_id=USER_ID,
        session_id=session_id,
        message=build_remote_message(state),
    ):
        summaries.append(_event_summary(event))
    fetched = await remote.async_get_session(user_id=USER_ID, session_id=session_id)
    return {
        "sessionId": session_id,
        "state": _session_state(fetched),
        "events": summaries,
    }


async def _verify_firestore(
    firestore_store: FirestoreStateStore,
    invocation: dict[str, Any],
    result_key: str,
) -> dict[str, Any]:
    state = invocation["state"]
    execution_id = str(state["executionId"])
    trace = await firestore_store.get_agent_execution(execution_id)
    if trace is None:
        raise AssertionError(f"Missing Firestore execution {execution_id}")
    result = state.get("lastResult") or {}
    evidence: dict[str, Any] = {
        "executionId": execution_id,
        "trace": _safe_trace_metadata(trace),
    }
    if result_key == "proposalId":
        resource_id = result.get("proposalId")
        proposal = await firestore_store.get_proposal(str(resource_id))
        if proposal is None:
            raise AssertionError(f"Missing Firestore proposal {resource_id}")
        evidence.update(
            {
                "proposalId": resource_id,
                "proposalStatus": proposal.get("status"),
                "proposalOriginAgent": proposal.get("originAgent"),
                "proposalExecutionId": proposal.get("agentExecutionId"),
                "proposalCorrelationId": proposal.get("correlationId"),
                "proposalModel": proposal.get("modelName"),
            }
        )
    else:
        resource_id = result.get("alertId")
        document = await firestore_store._sub("coverage_alerts").document(
            str(resource_id)
        ).get()
        if not document.exists:
            raise AssertionError(f"Missing Firestore coverage alert {resource_id}")
        alert = document.to_dict()
        evidence.update(
            {
                "alertId": resource_id,
                "alertStatus": alert.get("status"),
                "alertSceneId": alert.get("sceneId"),
                "missingShotIds": alert.get("missingShotIds"),
            }
        )
    return evidence


def _assert_schedule(invocation: dict[str, Any], evidence: dict[str, Any]) -> None:
    state = invocation["state"]
    assert state["toolAttempted"] is True
    assert state["proposalCreated"] is True
    assert state["lastErrorCode"] is None
    assert evidence["proposalStatus"] == "PENDING"
    assert evidence["proposalOriginAgent"] == "SCHEDULE_AGENT"
    assert evidence["proposalExecutionId"] == state["executionId"]
    assert evidence["proposalCorrelationId"] == state["event"]["correlationId"]
    assert evidence["proposalModel"] == MODEL_NAME
    assert evidence["trace"]["status"] == "SUCCESS"
    assert evidence["trace"]["agentName"] == "SCHEDULE_AGENT"
    assert evidence["trace"]["modelName"] == MODEL_NAME


def _safe_trace_metadata(trace: dict[str, Any]) -> dict[str, Any]:
    """Select the approved operational trace fields; exclude prompts and CoT."""
    return {
        key: trace.get(key)
        for key in (
            "executionId",
            "correlationId",
            "agentName",
            "modelName",
            "eventId",
            "startedAt",
            "completedAt",
            "durationMs",
            "toolCalls",
            "status",
            "errorCode",
            "evidenceReferences",
            "shortRationale",
        )
    }


async def main_async(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parents[2]
    client = agentplatform.Client(project=PROJECT_ID, location=AGENT_ENGINE_LOCATION)
    resource_name = args.resource
    if not resource_name:
        matches = [
            item
            for item in client.agent_engines.list()
            if getattr(item, "display_name", None) == DISPLAY_NAME
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one {DISPLAY_NAME} Agent Engine, found {len(matches)}"
            )
        resource_name = _resource_name(matches[0])
    remote = client.agent_engines.get(name=resource_name)
    operation_schemas = remote.operation_schemas() or []
    operation_names = sorted(
        str(item.get("name")) for item in operation_schemas if item.get("name")
    )

    store = _load_store(project_root)
    firestore_store = FirestoreStateStore(PROJECT_ID, PRODUCTION_NAMESPACE)
    try:
        _complete_scene_in_memory(store, "SC_01")
        act02_event = _event(
            store,
            EventType.ACTOR_DELAYED,
            {"actorId": "ACT_02", "delayMinutes": 45, "reason": "traffic delay"},
            f"agent-engine-3b-act02-{datetime.utcnow():%Y%m%d%H%M%S}",
        )
        act02 = await _invoke(remote, build_schedule_session_state(store, act02_event))
        act02_firestore = await _verify_firestore(firestore_store, act02, "proposalId")
        _assert_schedule(act02, act02_firestore)

        _complete_scene_in_memory(store, "SC_02")
        act03_event = _event(
            store,
            EventType.ACTOR_DELAYED,
            {"actorId": "ACT_03", "delayMinutes": 30, "reason": "unit transport delay"},
            f"agent-engine-3b-act03-{datetime.utcnow():%Y%m%d%H%M%S}",
        )
        act03 = await _invoke(remote, build_schedule_session_state(store, act03_event))
        act03_firestore = await _verify_firestore(firestore_store, act03, "proposalId")
        _assert_schedule(act03, act03_firestore)

        completed_shot = store.shots["SH_11"]
        store.shots["SH_11"] = completed_shot.model_copy(
            update={"status": ShotStatus.COMPLETE}
        )
        coverage_event = _event(
            store,
            EventType.SHOT_COMPLETED,
            {"sceneId": "SC_05", "shotId": "SH_11"},
            f"agent-engine-3b-coverage-{datetime.utcnow():%Y%m%d%H%M%S}",
        )
        coverage_no_tool_sessions: list[str] = []
        for _ in range(3):
            coverage = await _invoke(
                remote,
                build_coverage_session_state(store, coverage_event),
            )
            if coverage["state"].get("toolAttempted") is True:
                break
            coverage_no_tool_sessions.append(coverage["sessionId"])
        else:
            raise AssertionError("Coverage Agent did not call its tool in three sessions")
        coverage_firestore = await _verify_firestore(
            firestore_store, coverage, "alertId"
        )
        coverage_state = coverage["state"]
        assert coverage_state["toolAttempted"] is True
        assert coverage_state["alertCreated"] is True
        assert coverage_state["lastErrorCode"] is None
        assert coverage_firestore["alertStatus"] == "OPEN"
        assert coverage_firestore["trace"]["status"] == "SUCCESS"
        assert coverage_firestore["trace"]["agentName"] == "COVERAGE_AGENT"
        assert coverage_firestore["trace"]["modelName"] == MODEL_NAME

        proposal_ids_before_failure = {
            item["proposalId"] for item in await firestore_store.list_proposals()
        }
        failure_state = build_schedule_session_state(store, act02_event)
        failure_state["context"]["eligibleScenes"] = [
            {
                "sceneId": "SC_DOES_NOT_EXIST",
                "title": "Authority rejection probe",
                "currentPosition": 2,
                "estimatedDurationMinutes": 10,
                "characterIds": [],
                "location": {
                    "locationId": "LOC_01",
                    "availableUntilTime": "20:00",
                    "daylightConstraint": False,
                    "daylightDeadlineTime": None,
                },
                "eligible": True,
            }
        ]
        failure_state["context"]["currentSchedule"] = [
            {
                "sceneId": "SC_DOES_NOT_EXIST",
                "position": 2,
                "plannedStartTime": "09:00",
                "estimatedDurationMinutes": 10,
            }
        ]
        failure_no_tool_sessions: list[str] = []
        for _ in range(3):
            failed = await _invoke(remote, failure_state)
            if failed["state"].get("toolAttempted") is True:
                break
            failure_no_tool_sessions.append(failed["sessionId"])
            failure_state = build_schedule_session_state(store, act02_event)
            failure_state["context"]["eligibleScenes"] = [
                {
                    "sceneId": "SC_DOES_NOT_EXIST",
                    "title": "Authority rejection probe",
                    "currentPosition": 2,
                    "estimatedDurationMinutes": 10,
                    "characterIds": [],
                    "location": {
                        "locationId": "LOC_01",
                        "availableUntilTime": "20:00",
                        "daylightConstraint": False,
                        "daylightDeadlineTime": None,
                    },
                    "eligible": True,
                }
            ]
            failure_state["context"]["currentSchedule"] = [
                {
                    "sceneId": "SC_DOES_NOT_EXIST",
                    "position": 2,
                    "plannedStartTime": "09:00",
                    "estimatedDurationMinutes": 10,
                }
            ]
        else:
            raise AssertionError("Failure probe did not call its tool in three sessions")
        failed_state = failed["state"]
        failed_trace = await firestore_store.get_agent_execution(
            str(failed_state["executionId"])
        )
        proposal_ids_after_failure = {
            item["proposalId"] for item in await firestore_store.list_proposals()
        }
        assert failed_state["toolAttempted"] is True
        assert failed_state["proposalCreated"] is False
        assert failed_state["lastErrorCode"] == "ToolServerError"
        assert failed_trace is not None and failed_trace["status"] == "ERROR"
        assert proposal_ids_after_failure == proposal_ids_before_failure

        sessions = _safe_session_summaries(
            await remote.async_list_sessions(user_id=USER_ID)
        )
        evidence = {
            "verifiedAt": datetime.utcnow().isoformat() + "Z",
            "agentEngineResource": resource_name,
            "displayName": DISPLAY_NAME,
            "region": AGENT_ENGINE_LOCATION,
            "model": MODEL_NAME,
            "operationSchemas": operation_names,
            "act02Maya45": {
                "remote": _safe_invocation_summary(act02),
                "firestore": act02_firestore,
            },
            "act03Daniel30": {
                "remote": _safe_invocation_summary(act03),
                "firestore": act03_firestore,
            },
            "coverageSC05": {
                "remote": _safe_invocation_summary(coverage),
                "firestore": coverage_firestore,
                "noToolSessionIds": coverage_no_tool_sessions,
            },
            "failureSafety": {
                "remote": _safe_invocation_summary(failed),
                "firestoreTrace": _safe_trace_metadata(failed_trace),
                "proposalMutationCount": len(
                    proposal_ids_after_failure - proposal_ids_before_failure
                ),
                "noToolSessionIds": failure_no_tool_sessions,
            },
            "sessions": sessions,
        }
        return evidence
    finally:
        await firestore_store.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource")
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()
    evidence = asyncio.run(main_async(args))
    rendered = json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True)
    if args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
