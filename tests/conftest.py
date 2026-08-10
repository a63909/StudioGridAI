"""Shared pytest fixtures for StudioGrid AI tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is on PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.api.core.event_bus import LocalEventBus
from services.api.db.local_store import LocalStateStore


@pytest.fixture
def store():
    """Fresh in-memory store loaded with LAST LIGHT dataset."""
    s = LocalStateStore()
    package_path = project_root / "demo" / "last_light" / "production_package.json"
    with open(package_path, encoding="utf-8") as f:
        data = json.load(f)
    s.load_from_production_package(data)

    # Set shoot day to ACTIVE
    from services.api.domain.enums import ShootDayStatus
    day = s.get_active_shoot_day()
    if day and s.production:
        updated = day.model_copy(update={"status": ShootDayStatus.ACTIVE})
        days = list(s.production.shootDays)
        days[0] = updated
        s.production = s.production.model_copy(update={"shootDays": days})
    return s


@pytest.fixture
def event_bus():
    return LocalEventBus()


@pytest.fixture
def registry(store, event_bus):
    from services.api.core.tool_registry import ToolRegistry
    return ToolRegistry(store=store, event_bus=event_bus)
