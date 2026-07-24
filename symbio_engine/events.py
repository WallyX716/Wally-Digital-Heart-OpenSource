"""Lightweight pub/sub event bus for host ↔ organism communication."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional


Handler = Callable[["Event"], None]


@dataclass
class Event:
    """A single event flowing through the organism."""

    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "host"
    timestamp: float = field(default_factory=time.time)
    tick: int = 0

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)


class EventBus:
    """Thread-safe event bus with history for butterfly-effect analysis."""

    def __init__(self, history_limit: int = 500) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._wildcard: List[Handler] = []
        self._history: Deque[Event] = deque(maxlen=history_limit)
        self._lock = threading.RLock()
        self._tick = 0

    @property
    def tick(self) -> int:
        return self._tick

    def on(self, event_name: str, handler: Handler) -> Callable[[], None]:
        """Subscribe to an event. Returns an unsubscribe callable."""
        with self._lock:
            if event_name == "*":
                self._wildcard.append(handler)
            else:
                self._handlers[event_name].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if event_name == "*":
                    if handler in self._wildcard:
                        self._wildcard.remove(handler)
                elif handler in self._handlers[event_name]:
                    self._handlers[event_name].remove(handler)

        return unsubscribe

    def emit(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "host",
    ) -> Event:
        """Publish an event to all matching subscribers."""
        with self._lock:
            self._tick += 1
            event = Event(
                name=name,
                payload=dict(payload or {}),
                source=source,
                tick=self._tick,
            )
            self._history.append(event)
            handlers = list(self._handlers.get(name, [])) + list(self._wildcard)

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Never let a subscriber crash the bus; organism healer may
                # still observe via history / external wrap.
                pass
        return event

    def history(
        self,
        name: Optional[str] = None,
        limit: int = 50,
    ) -> List[Event]:
        with self._lock:
            items = list(self._history)
        if name is not None:
            items = [e for e in items if e.name == name]
        return items[-limit:]

    def recent_names(self, limit: int = 20) -> List[str]:
        return [e.name for e in self.history(limit=limit)]

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()
