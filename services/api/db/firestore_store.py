"""Firestore persistence adapter for the StudioGrid demo namespace.

The application remains the state authority used by agents and tools. This
adapter is called only by the FastAPI Tool Server and mirrors validated state,
events, proposals, alerts, and safe execution traces to Firestore.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import google.auth
from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient, Query

from ..domain.events import ProductionEvent
from ..domain.models import AgentExecution, CoverageAlert, ScheduleProposal

logger = logging.getLogger(__name__)


def _get_firestore_client(project_id: str, database: str = "(default)") -> AsyncClient:
    """Build an ADC client while explicitly assigning the application quota project."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
        quota_project_id=project_id,
    )
    return firestore.AsyncClient(
        project=project_id,
        database=database,
        credentials=credentials,
    )


class FirestoreStateStore:
    """Namespaced durable mirror under ``productions/{production_id}``."""

    COLLECTION = "productions"
    DEMO_PRODUCTION_ID = "last-light-demo"

    def __init__(
        self,
        project_id: str,
        production_id: str,
        database: str = "(default)",
    ) -> None:
        if not production_id or "/" in production_id:
            raise ValueError("production_id must be a single non-empty Firestore document ID")
        self.project_id = project_id
        self.production_id = production_id
        self.database = database
        self._db = _get_firestore_client(project_id, database)

    def _root(self):
        return self._db.collection(self.COLLECTION).document(self.production_id)

    def _sub(self, subcollection: str):
        return self._root().collection(subcollection)

    async def healthcheck(self) -> None:
        """Perform a real namespaced Firestore read without mutating data."""
        await self._root().get()

    async def save_application_state(self, store: Any) -> None:
        """Persist the validated in-memory application state as one atomic document."""
        production = store.production.model_dump(mode="json") if store.production else None
        payload = {
            "productionId": self.production_id,
            "sourceProductionId": store.production.productionId if store.production else None,
            "savedAt": datetime.utcnow().isoformat(),
            "production": production,
            "actors": [item.model_dump(mode="json") for item in store.actors.values()],
            "locations": [item.model_dump(mode="json") for item in store.locations.values()],
            "props": [item.model_dump(mode="json") for item in store.props.values()],
            "scenes": [item.model_dump(mode="json") for item in store.scenes.values()],
            "shots": [item.model_dump(mode="json") for item in store.shots.values()],
            "totalDelayMinutes": store._total_delay_minutes,
            "recoveredMinutes": store._recovered_minutes,
        }
        await self._root().set(
            {
                "productionId": self.production_id,
                "sourceProductionId": payload["sourceProductionId"],
                "updatedAt": payload["savedAt"],
            },
            merge=True,
        )
        await self._sub("state").document("current").set(payload)

    async def save_agent_execution(self, execution: AgentExecution) -> None:
        await self._sub("agent_executions").document(execution.executionId).set(
            execution.model_dump(mode="json")
        )

    async def get_agent_execution(self, execution_id: str) -> dict[str, Any] | None:
        doc = await self._sub("agent_executions").document(execution_id).get()
        return doc.to_dict() if doc.exists else None

    async def get_agent_executions(
        self, agent_name: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        query = self._sub("agent_executions").order_by(
            "startedAt", direction=Query.DESCENDING
        ).limit(limit)
        if agent_name:
            query = query.where(filter=firestore.FieldFilter("agentName", "==", agent_name))
        docs = await query.get()
        return [doc.to_dict() for doc in docs]

    async def save_proposal(self, proposal: ScheduleProposal) -> None:
        await self._sub("proposals").document(proposal.proposalId).set(
            proposal.model_dump(mode="json")
        )

    async def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        doc = await self._sub("proposals").document(proposal_id).get()
        return doc.to_dict() if doc.exists else None

    async def list_proposals(self) -> list[dict[str, Any]]:
        docs = await self._sub("proposals").get()
        return [doc.to_dict() for doc in docs]

    async def save_coverage_alert(self, alert: CoverageAlert) -> None:
        await self._sub("coverage_alerts").document(alert.alertId).set(
            alert.model_dump(mode="json")
        )

    async def save_event(self, event: ProductionEvent) -> None:
        await self._sub("events").document(event.eventId).set(event.model_dump(mode="json"))

    async def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        docs = await self._sub("events").order_by(
            "timestamp", direction=Query.DESCENDING
        ).limit(limit).get()
        return [doc.to_dict() for doc in docs]

    async def cleanup_demo_data(self) -> int:
        """Delete only known collections in the explicit StudioGrid demo namespace.

        This method is never called automatically. The production ID guard prevents
        cleanup code from being pointed at another production.
        """
        if self.production_id != self.DEMO_PRODUCTION_ID:
            raise ValueError("Cleanup is restricted to productionId=last-light-demo")
        deleted = 0
        for name in (
            "agent_executions",
            "coverage_alerts",
            "events",
            "proposals",
            "state",
        ):
            docs = await self._sub(name).get()
            for doc in docs:
                await doc.reference.delete()
                deleted += 1
        await self._root().delete()
        return deleted

    async def close(self) -> None:
        self._db.close()
