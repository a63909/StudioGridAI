"""Scenes router."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..domain.models import Scene

router = APIRouter()


@router.get("/", response_model=list[Scene])
async def list_scenes(request: Request):
    store = request.app.state.store
    scenes = list(store.scenes.values())
    # Recompute status from actual state
    updated = []
    for sc in scenes:
        computed = store.compute_scene_status(sc.sceneId)
        updated.append(sc.model_copy(update={"status": computed}))
    return updated


@router.get("/{scene_id}", response_model=Scene)
async def get_scene(scene_id: str, request: Request):
    store = request.app.state.store
    scene = store.scenes.get(scene_id)
    if scene is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Scene {scene_id} not found")
    computed = store.compute_scene_status(scene_id)
    return scene.model_copy(update={"status": computed})


@router.get("/{scene_id}/coverage")
async def get_scene_coverage(scene_id: str, request: Request):
    store = request.app.state.store
    return store.compute_coverage(scene_id).model_dump()
