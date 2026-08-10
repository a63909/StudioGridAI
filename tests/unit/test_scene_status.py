"""Tests for scene status computation and dependencies."""
import pytest

from services.api.domain.enums import SceneStatus, ShotStatus


def test_scene_starts_planned(store):
    scene = store.scenes["SC_01"]
    status = store.compute_scene_status("SC_01")
    assert status == SceneStatus.PLANNED


def test_scene_blocked_when_dependency_incomplete(store):
    """SC_02 depends on SC_01. SC_01 not complete → SC_02 blocked."""
    status = store.compute_scene_status("SC_02")
    assert status == SceneStatus.BLOCKED


def test_scene_not_blocked_when_no_dependencies(store):
    """SC_01 has no dependencies — should be PLANNED not BLOCKED."""
    status = store.compute_scene_status("SC_01")
    assert status != SceneStatus.BLOCKED


def test_scene_partial_when_some_shots_complete(store):
    """Complete some but not all shots for a scene → PARTIAL."""
    # SC_01 has 3 shots: SH_01, SH_02, SH_03
    # Complete just SH_01
    shot = store.shots["SH_01"]
    in_progress = shot.model_copy(update={"status": ShotStatus.IN_PROGRESS})
    store.upsert_shot(in_progress)
    complete = in_progress.model_copy(update={"status": ShotStatus.COMPLETE})
    store.upsert_shot(complete)

    status = store.compute_scene_status("SC_01")
    assert status == SceneStatus.PARTIAL


def test_scene_complete_when_all_shots_complete(store):
    """All shots for SC_01 complete → scene is COMPLETE."""
    for shot_id in ["SH_01", "SH_02", "SH_03"]:
        shot = store.shots[shot_id]
        store.upsert_shot(shot.model_copy(update={"status": ShotStatus.IN_PROGRESS}))
        store.upsert_shot(shot.model_copy(update={"status": ShotStatus.COMPLETE}))

    status = store.compute_scene_status("SC_01")
    assert status == SceneStatus.COMPLETE


def test_dependency_chain(store):
    """SC_05 depends on SC_02 and SC_04. Neither complete → SC_05 blocked."""
    status = store.compute_scene_status("SC_05")
    assert status == SceneStatus.BLOCKED
