"""Firestore cleanup script for StudioGrid AI demo data.

Deletes ONLY the last-light-demo production data from Firestore.
NEVER deletes the database or other productions.

Usage:
    python -m agents.google_adk.cleanup_demo

This removes:
    productions/last-light-demo/agent_executions/*
    productions/last-light-demo/coverage_alerts/*
    productions/last-light-demo/proposals/*
    productions/last-light-demo/events/*
    productions/last-light-demo/state/*
    productions/last-light-demo  (document)
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "studiogrid-ai")

DEMO_PRODUCTION_ID = "last-light-demo"


async def main() -> None:
    from services.api.db.firestore_store import FirestoreStateStore

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "studiogrid-ai")
    print(f"Cleaning demo data:")
    print(f"  Project: {project_id}")
    print(f"  Production: {DEMO_PRODUCTION_ID}")
    print(f"  Database: (default)")
    print()

    store = FirestoreStateStore(
        project_id=project_id,
        production_id=DEMO_PRODUCTION_ID,
    )

    try:
        deleted = await store.cleanup_demo_data()
    finally:
        await store.close()
    print(f"Deleted {deleted} documents.")
    print("Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(main())
