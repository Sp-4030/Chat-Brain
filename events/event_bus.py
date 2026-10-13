"""Thread-safe In-Memory Event Bus for ChatBrain.

Dispatches events from readers to listeners with error isolation.
"""

from __future__ import annotations

import threading
from typing import Callable, Dict, List, Optional, Type
from events.base_event import BaseEvent
from utils.logger import get_logger

logger = get_logger("EventBus")


class EventBus:
    """Thread-safe publish-subscribe event bus."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable[[BaseEvent], None]]] = {}

    def subscribe(
        self,
        event_type: Type[BaseEvent] | str,
        handler: Callable[[Any], None],
    ) -> None:
        """Register a handler for a specific event type."""
        type_key = event_type if isinstance(event_type, str) else event_type.__name__
        with self._lock:
            if type_key not in self._subscribers:
                self._subscribers[type_key] = []
            if handler not in self._subscribers[type_key]:
                self._subscribers[type_key].append(handler)
                logger.debug("Subscribed handler %s to event %s", handler.__name__, type_key)

    def unsubscribe(
        self,
        event_type: Type[BaseEvent] | str,
        handler: Callable[[Any], None],
    ) -> None:
        """Unregister a handler from an event type."""
        type_key = event_type if isinstance(event_type, str) else event_type.__name__
        with self._lock:
            if type_key in self._subscribers and handler in self._subscribers[type_key]:
                self._subscribers[type_key].remove(handler)
                logger.debug("Unsubscribed handler %s from event %s", handler.__name__, type_key)

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all registered subscribers with error isolation."""
        type_key = event.event_type
        handlers: List[Callable[[BaseEvent], None]] = []

        with self._lock:
            if type_key in self._subscribers:
                handlers = list(self._subscribers[type_key])

        if not handlers:
            logger.debug("No subscribers found for event %s", type_key)
            return

        for handler in handlers:
            try:
                handler(event)
            except Exception as err:
                logger.error(
                    "Error executing handler '%s' for event '%s': %s",
                    getattr(handler, "__name__", str(handler)),
                    type_key,
                    err,
                    exc_info=True,
                )


_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Singleton getter for EventBus."""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance
