"""Tests for coverage calculation."""
import pytest

from services.api.domain.enums import ShotStatus


def test_coverage_all_planned(store):
    """All shots planned → 0% coverage, all missing."""
    stats = store.compute_coverage("SC_08")
    assert stats.plannedShotCount == 4  # SH_18, SH_19, SH_20, SH_21
    assert stats.completedShotCount == 0
    assert stats.coveragePercent == 0.0
    assert len(stats.missingShotIds) == 4


def test_coverage_partial(store):
    """Complete 2 of 4 SC_08 shots → 50% coverage."""
    for shot_id in ["SH_18", "SH_19"]:
        shot = store.shots[shot_id]
        store.upsert_shot(shot.model_copy(update={"status": ShotStatus.IN_PROGRESS}))
        store.upsert_shot(shot.model_copy(update={"status": ShotStatus.COMPLETE}))

    stats = store.compute_coverage("SC_08")
    assert stats.completedShotCount == 2
    assert stats.coveragePercent == 50.0
    assert set(stats.missingShotIds) == {"SH_20", "SH_21"}


def test_coverage_complete(store):
    """All 4 SC_08 shots complete → 100% coverage, no missing."""
    for shot_id in ["SH_18", "SH_19", "SH_20", "SH_21"]:
        shot = store.shots[shot_id]
        store.upsert_shot(shot.model_copy(update={"status": ShotStatus.IN_PROGRESS}))
        store.upsert_shot(shot.model_copy(update={"status": ShotStatus.COMPLETE}))

    stats = store.compute_coverage("SC_08")
    assert stats.coveragePercent == 100.0
    assert stats.missingShotIds == []


def test_coverage_percent_calculation(store):
    """Coverage percent rounds to 1 decimal place."""
    # SC_01 has 3 shots. Complete 1 → 33.3%
    shot = store.shots["SH_01"]
    store.upsert_shot(shot.model_copy(update={"status": ShotStatus.IN_PROGRESS}))
    store.upsert_shot(shot.model_copy(update={"status": ShotStatus.COMPLETE}))

    stats = store.compute_coverage("SC_01")
    assert stats.completedShotCount == 1
    assert stats.plannedShotCount == 3
    assert stats.coveragePercent == round(1 / 3 * 100, 1)
