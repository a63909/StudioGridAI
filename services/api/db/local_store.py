"""In-memory state store for StudioGrid AI Phase 1.

Holds the full production state in memory for local development and testing.
Designed to be replaced by FirestoreStateStore in Phase 2 without changing
the interface used by the Tool Registry.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from ..domain.enums import (
    AgentMode,
    AlertStatus,
    OriginType,
    PartnerIntegrationStatus,
    SceneStatus,
    ShotStatus,
    ShootDayStatus,
)
from ..domain.events import ProductionEvent
from ..domain.models import (
    Actor,
    AgentExecution,
    ContinuityAlert,
    ContinuityFact,
    CoverageAlert,
    CoverageStats,
    DashboardStats,
    Location,
    Production,
    Prop,
    Risk,
    Scene,
    ScheduleProposal,
    ScheduledScene,
    Shot,
    ShootDay,
    WrapReport,
)


class LocalStateStore:
    """In-memory production state store.

    All state is held in Python dicts keyed by entity ID.
    Thread-safety: not thread-safe — single-process async use only.
    """

    def __init__(self) -> None:
        self.production: Production | None = None
        self.actors: dict[str, Actor] = {}
        self.locations: dict[str, Location] = {}
        self.props: dict[str, Prop] = {}
        self.scenes: dict[str, Scene] = {}
        self.shots: dict[str, Shot] = {}
        self.events: list[ProductionEvent] = []
        self.agent_executions: dict[str, AgentExecution] = {}
        self.proposals: dict[str, ScheduleProposal] = {}
        self.continuity_facts: dict[str, ContinuityFact] = {}
        self.continuity_alerts: dict[str, ContinuityAlert] = {}
        self.coverage_alerts: dict[str, CoverageAlert] = {}
        self.risks: dict[str, Risk] = {}
        self.wrap_report: WrapReport | None = None
        self._total_delay_minutes: int = 0
        self._recovered_minutes: int = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Load from production package
    # ─────────────────────────────────────────────────────────────────────────

    def load_from_production_package(self, data: dict[str, Any]) -> None:
        """Load a full production package JSON into the store."""
        from ..domain.models import ShootDay, ScheduledScene

        # Production
        schedule = data.get("shootingSchedule", {})
        shoot_day = ShootDay(
            shootDayId=schedule.get("shootDayId", "DAY_001"),
            productionId=data["productionId"],
            date=schedule.get("date", "2025-07-15"),
            status=ShootDayStatus.PLANNED,
            scheduledScenes=[
                ScheduledScene(**s) for s in schedule.get("scheduledScenes", [])
            ],
        )
        self.production = Production(
            productionId=data["productionId"],
            title=data["title"],
            shootDays=[shoot_day],
        )

        # Actors
        for a in data.get("actors", []):
            actor = Actor(**{k: v for k, v in a.items() if k in Actor.model_fields})
            self.actors[actor.actorId] = actor

        # Locations
        for loc in data.get("locations", []):
            location = Location(**{k: v for k, v in loc.items() if k in Location.model_fields})
            self.locations[location.locationId] = location

        # Props
        for p in data.get("props", []):
            prop = Prop(**{k: v for k, v in p.items() if k in Prop.model_fields})
            self.props[prop.propId] = prop

        # Scenes
        for s in data.get("scenes", []):
            scene_data = {k: v for k, v in s.items() if k in Scene.model_fields}
            scene = Scene(**scene_data)
            self.scenes[scene.sceneId] = scene
            # Pre-load continuity facts from script
            for fact_data in s.get("continuityFacts", []):
                fact = ContinuityFact(**fact_data)
                self.continuity_facts[fact.factId] = fact

        # Shots
        for sh in data.get("shots", []):
            shot_data = {k: v for k, v in sh.items() if k in Shot.model_fields}
            shot = Shot(**shot_data)
            self.shots[shot.shotId] = shot

    def restore_application_state(self, data: dict[str, Any]) -> None:
        """Overlay a validated durable state after loading static seed metadata."""
        production = data.get("production")
        if production is not None:
            self.production = Production.model_validate(production)

        model_sets = (
            ("actors", Actor, "actorId"),
            ("locations", Location, "locationId"),
            ("props", Prop, "propId"),
            ("scenes", Scene, "sceneId"),
            ("shots", Shot, "shotId"),
        )
        for field_name, model_type, id_field in model_sets:
            if field_name not in data:
                continue
            restored = [model_type.model_validate(item) for item in data[field_name]]
            setattr(self, field_name, {getattr(item, id_field): item for item in restored})

        self._total_delay_minutes = int(data.get("totalDelayMinutes", 0))
        self._recovered_minutes = int(data.get("recoveredMinutes", 0))

    # ─────────────────────────────────────────────────────────────────────────
    # Event log
    # ─────────────────────────────────────────────────────────────────────────

    def add_event(self, event: ProductionEvent) -> None:
        self.events.append(event)

    def get_events(self) -> list[ProductionEvent]:
        return list(self.events)

    def upsert_agent_execution(self, execution: AgentExecution) -> None:
        self.agent_executions[execution.executionId] = execution

    def get_agent_execution(self, execution_id: str) -> AgentExecution | None:
        return self.agent_executions.get(execution_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Upserts
    # ─────────────────────────────────────────────────────────────────────────

    def upsert_actor(self, actor: Actor) -> None:
        self.actors[actor.actorId] = actor

    def upsert_location(self, location: Location) -> None:
        self.locations[location.locationId] = location

    def upsert_shot(self, shot: Shot) -> None:
        self.shots[shot.shotId] = shot

    def upsert_scene(self, scene: Scene) -> None:
        self.scenes[scene.sceneId] = scene

    def upsert_proposal(self, proposal: ScheduleProposal) -> None:
        self.proposals[proposal.proposalId] = proposal

    def upsert_continuity_fact(self, fact: ContinuityFact) -> None:
        self.continuity_facts[fact.factId] = fact

    def upsert_continuity_alert(self, alert: ContinuityAlert) -> None:
        self.continuity_alerts[alert.alertId] = alert

    def upsert_coverage_alert(self, alert: CoverageAlert) -> None:
        self.coverage_alerts[alert.alertId] = alert

    def upsert_risk(self, risk: Risk) -> None:
        self.risks[risk.riskId] = risk

    # ─────────────────────────────────────────────────────────────────────────
    # Computed statistics — never hardcoded
    # ─────────────────────────────────────────────────────────────────────────

    def compute_coverage(self, scene_id: str) -> CoverageStats:
        """Calculate coverage stats for a scene from actual shot state."""
        scene_shots = [s for s in self.shots.values() if s.sceneId == scene_id]
        planned = len(scene_shots)
        completed = sum(1 for s in scene_shots if s.status == ShotStatus.COMPLETE)
        missing = [s.shotId for s in scene_shots if s.status not in {ShotStatus.COMPLETE, ShotStatus.SKIPPED}]
        coverage_pct = (completed / planned * 100.0) if planned > 0 else 0.0
        return CoverageStats(
            sceneId=scene_id,
            plannedShotCount=planned,
            completedShotCount=completed,
            missingShotIds=missing,
            coveragePercent=round(coverage_pct, 1),
        )

    def compute_scene_status(self, scene_id: str) -> SceneStatus:
        """Derive scene status from shot state and dependency state."""
        return self._compute_scene_status(scene_id, set())

    def _compute_scene_status(self, scene_id: str, visiting: set[str]) -> SceneStatus:
        """Dependency-aware status calculation with cycle protection."""
        scene = self.scenes.get(scene_id)
        if scene is None:
            return SceneStatus.PLANNED
        if scene_id in visiting:
            return SceneStatus.BLOCKED
        visiting = {*visiting, scene_id}

        # Check dependencies
        for dep in scene.dependencies:
            dep_scene = self.scenes.get(dep.dependsOnSceneId)
            if dep_scene and self._compute_scene_status(dep.dependsOnSceneId, visiting) != SceneStatus.COMPLETE:
                return SceneStatus.BLOCKED

        scene_shots = [s for s in self.shots.values() if s.sceneId == scene_id]
        if not scene_shots:
            return SceneStatus.PLANNED

        statuses = {s.status for s in scene_shots}

        if all(s.status == ShotStatus.COMPLETE for s in scene_shots):
            return SceneStatus.COMPLETE

        if any(s.status == ShotStatus.IN_PROGRESS for s in scene_shots):
            return SceneStatus.IN_PROGRESS

        if any(s.status == ShotStatus.COMPLETE for s in scene_shots):
            return SceneStatus.PARTIAL

        return SceneStatus.PLANNED

    def compute_dashboard_stats(self, shoot_day_id: str) -> DashboardStats:
        """Calculate dashboard statistics from actual state — never hardcoded."""
        all_shots = list(self.shots.values())
        all_scenes = list(self.scenes.values())

        planned_shots = len(all_shots)
        completed_shots = sum(1 for s in all_shots if s.status == ShotStatus.COMPLETE)
        failed_shots = sum(1 for s in all_shots if s.status == ShotStatus.FAILED)

        planned_scenes = len(all_scenes)
        completed_scenes = sum(
            1 for sc in all_scenes
            if self.compute_scene_status(sc.sceneId) == SceneStatus.COMPLETE
        )
        partial_scenes = sum(
            1 for sc in all_scenes
            if self.compute_scene_status(sc.sceneId) == SceneStatus.PARTIAL
        )
        blocked_scenes = sum(
            1 for sc in all_scenes
            if self.compute_scene_status(sc.sceneId) == SceneStatus.BLOCKED
        )

        open_continuity = sum(
            1 for a in self.continuity_alerts.values()
            if a.status == AlertStatus.OPEN
        )
        open_coverage = sum(
            1 for a in self.coverage_alerts.values()
            if a.status == AlertStatus.OPEN
        )
        pending_proposals = sum(
            1 for p in self.proposals.values()
            if p.status.value == "PENDING"
        )
        at_risk = sum(
            1 for r in self.risks.values()
            if r.status.value in {"ACTIVE", "MONITORING"}
        )

        return DashboardStats(
            shootDayId=shoot_day_id,
            plannedShotCount=planned_shots,
            completedShotCount=completed_shots,
            failedShotCount=failed_shots,
            plannedSceneCount=planned_scenes,
            completedSceneCount=completed_scenes,
            partialSceneCount=partial_scenes,
            blockedSceneCount=blocked_scenes,
            atRiskCount=at_risk,
            openContinuityAlerts=open_continuity,
            openCoverageAlerts=open_coverage,
            pendingProposals=pending_proposals,
            totalDelayMinutes=self._total_delay_minutes,
            estimatedMinutesRecovered=self._recovered_minutes,
            agentMode=AgentMode.DEV,
            partnerStatus=PartnerIntegrationStatus.NOT_CONFIGURED,
        )

    def add_delay_minutes(self, minutes: int) -> None:
        self._total_delay_minutes += minutes

    def add_recovered_minutes(self, minutes: int) -> None:
        self._recovered_minutes += minutes

    # ─────────────────────────────────────────────────────────────────────────
    # Shoot day helpers
    # ─────────────────────────────────────────────────────────────────────────

    def get_active_shoot_day(self) -> ShootDay | None:
        if self.production is None:
            return None
        for day in self.production.shootDays:
            if day.status in {ShootDayStatus.ACTIVE, ShootDayStatus.PLANNED}:
                return day
        return None

    def update_schedule_order(self, shoot_day_id: str, new_order: list[ScheduledScene]) -> None:
        """Update the scheduled scene order after an approved proposal."""
        if self.production is None:
            return
        for day in self.production.shootDays:
            if day.shootDayId == shoot_day_id:
                updated = day.model_copy(update={"scheduledScenes": new_order})
                idx = self.production.shootDays.index(day)
                days = list(self.production.shootDays)
                days[idx] = updated
                self.production = self.production.model_copy(update={"shootDays": days})
                return

    # ─────────────────────────────────────────────────────────────────────────
    # Blocked scenes (actor availability)
    # ─────────────────────────────────────────────────────────────────────────

    def get_scenes_blocked_by_actor(self, actor_id: str) -> list[str]:
        """Return scene IDs that require this actor and are not yet complete."""
        actor = self.actors.get(actor_id)
        if actor is None:
            return []
        return [
            scene.sceneId
            for scene in self.scenes.values()
            if actor_id in scene.characterIds
            and self.compute_scene_status(scene.sceneId) != SceneStatus.COMPLETE
        ]

    def get_shootable_scenes_without_actor(self, actor_id: str) -> list[str]:
        """Return scene IDs that CAN be shot right now despite the missing actor."""
        return [
            scene.sceneId
            for scene in self.scenes.values()
            if actor_id not in scene.characterIds
            and self.compute_scene_status(scene.sceneId) not in {
                SceneStatus.COMPLETE,
                SceneStatus.BLOCKED,
            }
            and self._scene_actors_available(scene.sceneId)
        ]

    def _scene_actors_available(self, scene_id: str) -> bool:
        """Check if all required actors for a scene are currently available."""
        scene = self.scenes.get(scene_id)
        if scene is None:
            return False
        for actor_id in scene.characterIds:
            actor = self.actors.get(actor_id)
            if actor and actor.currentStatus.value in {"DELAYED", "UNAVAILABLE"}:
                return False
        return True

    def clear(self) -> None:
        """Reset all state. Used in tests."""
        self.__init__()
