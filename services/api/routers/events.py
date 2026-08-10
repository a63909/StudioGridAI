"""Events router — event log and SSE stream."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/")
async def list_events(request: Request, limit: int = 100):
    store = request.app.state.store
    events = store.get_events()
    return [e.model_dump(mode="json") for e in events[-limit:]]


@router.get("/stream")
async def stream_events(request: Request):
    """Server-Sent Events stream for real-time production events."""
    store = request.app.state.store
    event_bus = request.app.state.event_bus

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()

        async def enqueue(event):
            await queue.put(event)

        event_bus.subscribe_all(enqueue)

        # Send current stats immediately
        day = store.get_active_shoot_day()
        shoot_day_id = day.shootDayId if day else "DAY_001"
        stats = store.compute_dashboard_stats(shoot_day_id)
        yield f"data: {json.dumps({'type': 'DASHBOARD_STATS', 'payload': stats.model_dump()})}\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    data = event.model_dump(mode="json")
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield "data: {\"type\": \"HEARTBEAT\"}\n\n"
        finally:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
