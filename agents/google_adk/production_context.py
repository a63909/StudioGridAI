"""Pure builders for factual production context supplied to Google ADK agents."""
from __future__ import annotations

from typing import Any

from services.api.db.local_store import LocalStateStore
from services.api.domain.events import ProductionEvent


def build_schedule_context(
    store: LocalStateStore,
    event: ProductionEvent,
) -> dict[str, Any]:
    """Build the server-computed schedule facts for one ACTOR_DELAYED event."""
    actor_id = str(event.payload["actorId"])
    day = store.get_active_shoot_day()
    position_by_scene = (
        {item.sceneId: item.position for item in day.scheduledScenes} if day else {}
    )
    eligible_scenes: list[dict[str, Any]] = []
    for scene in store.scenes.values():
        position = position_by_scene.get(scene.sceneId)
        location = store.locations.get(scene.locationId)
        eligible = (
            position is not None
            and position > 1
            and actor_id not in scene.characterIds
            and store._scene_actors_available(scene.sceneId)
            and store.compute_scene_status(scene.sceneId).value not in {"COMPLETE", "BLOCKED"}
            and location is not None
            and location.status.value == "AVAILABLE"
        )
        if eligible:
            eligible_scenes.append(
                {
                    "sceneId": scene.sceneId,
                    "title": scene.title,
                    "currentPosition": position,
                    "estimatedDurationMinutes": scene.estimatedDurationMinutes,
                    "characterIds": scene.characterIds,
                    "location": {
                        "locationId": location.locationId,
                        "availableUntilTime": location.availableUntilTime,
                        "daylightConstraint": location.daylightConstraint,
                        "daylightDeadlineTime": location.daylightDeadlineTime,
                    },
                    "eligible": True,
                }
            )

    actor = store.actors.get(actor_id)
    return {
        "classification": {
            "event": "FACT",
            "eligibility": "FACT",
            "agentOutput": "RECOMMENDATION",
            "approval": "HUMAN_DECISION_ONLY",
        },
        "event": {
            "eventId": event.eventId,
            "type": event.type.value,
            "actorId": actor_id,
            "actorName": actor.name if actor else event.payload.get("actorName"),
            "delayMinutes": event.payload.get("delayMinutes", 0),
            "untrustedProductionNote": event.payload.get("reason", ""),
        },
        "shootDayId": day.shootDayId if day else event.shootDayId,
        "currentSchedule": [
            item.model_dump(mode="json") for item in day.scheduledScenes
        ] if day else [],
        "blockedSceneIds": store.get_scenes_blocked_by_actor(actor_id),
        "eligibleScenes": eligible_scenes,
    }


def build_coverage_context(store: LocalStateStore, scene_id: str) -> dict[str, Any]:
    """Build factual planned/completed/missing shot sets for one scene."""
    scene = store.scenes[scene_id]
    shots = [shot for shot in store.shots.values() if shot.sceneId == scene_id]
    return {
        "sceneId": scene_id,
        "classification": {
            "plannedAndCompletedShots": "FACT",
            "editSufficiency": "INFERENCE",
        },
        "FACT_plannedShotIds": [shot.shotId for shot in shots],
        "FACT_completedShotIds": [
            shot.shotId for shot in shots if shot.status.value == "COMPLETE"
        ],
        "FACT_missingShotIds": [
            shot.shotId
            for shot in shots
            if shot.status.value not in {"COMPLETE", "SKIPPED"}
        ],
        "untrustedSceneDescription": scene.description,
    }
