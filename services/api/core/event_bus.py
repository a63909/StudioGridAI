"""Event Bus for StudioGrid AI.

LocalEventBus: in-process pub/sub for Phase 1 development and testing.
Interface designed for Cloud Pub/Sub replacement in Phase 2.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Awaitable

from ..domain.events import ProductionEvent
from ..domain.enums import EventType

logger = logging.getLogger(__name__)

EventHandler = Callable[[ProductionEvent], Awaitable[None]]


class EventBus(ABC):
    """Abstract event bus interface.

    Phase 1: LocalEventBus (in-process)
    Phase 2: Cloud Pub/Sub implementation (same interface, different transport)
    """

    @abstractmethod
    async def publish(self, event: ProductionEvent) -> None:
        """Publish an event to all subscribers."""
        ...

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        ...

    @abstractmethod
    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all event types."""
        ...


class LocalEventBus(EventBus):
    """In-process event bus for Phase 1 development and testing.

    Thread-safety: not thread-safe. For single-process async usage only.
    All handlers are called concurrently via asyncio.gather.
    Exceptions from individual handlers are logged but do not stop other handlers.
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []
        self._event_log: list[ProductionEvent] = []

    async def publish(self, event: ProductionEvent) -> None:
        self._event_log.append(event)
        logger.debug(
            "event_published",
            extra={
                "eventId": event.eventId,
                "type": event.type,
                "correlationId": event.correlationId,
                "source": event.source,
            },
        )

        handlers = list(self._handlers.get(event.type, [])) + list(self._wildcard_handlers)
        if not handlers:
            return

        results = await asyncio.gather(
            *[h(event) for h in handlers],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "event_handler_error",
                    extra={
                        "eventId": event.eventId,
                        "eventType": event.type,
                        "handlerIndex": i,
                        "error": str(result),
                    },
                    exc_info=result,
                )

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._wildcard_handlers.append(handler)

    def get_event_log(self) -> list[ProductionEvent]:
        """Return a copy of all published events in order."""
        return list(self._event_log)

    def clear(self) -> None:
        """Reset all state. Used in tests."""
        self._event_log.clear()
        self._handlers.clear()
        self._wildcard_handlers.clear()
