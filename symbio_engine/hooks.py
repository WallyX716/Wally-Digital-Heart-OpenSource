"""
Integration hooks for host programs and Pygame games.

Three patterns:

1. ``@symbio_hook`` / ``engine.hook`` — decorate callables so they auto-feed
   the organism and gain self-healing.
2. ``on_event`` — subscribe to organism/bus events from the host side.
3. ``host_callback`` — register host functions the organism can invoke
   (symbiotic reverse hooks).
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# Module-level default engine reference set by SymbioEngine.attach_globals().
_DEFAULT_ENGINE: Any = None


def set_default_engine(engine: Any) -> None:
    global _DEFAULT_ENGINE
    _DEFAULT_ENGINE = engine


def get_default_engine() -> Any:
    return _DEFAULT_ENGINE


def symbio_hook(
    event_name: str = "interaction",
    *,
    intensity: float = 0.4,
    heal: bool = True,
    default: Any = None,
    engine: Any = None,
    label: str = "",
) -> Callable[[F], F]:
    """
    Decorator: run the function under SymbioEngine protection and emit an event.

    Usage::

        engine = SymbioEngine()
        engine.attach_globals()

        @symbio_hook("player_action", intensity=0.5)
        def jump():
            ...
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            eng = engine or _DEFAULT_ENGINE
            fn_label = label or getattr(fn, "__name__", "hooked")
            if eng is None:
                return fn(*args, **kwargs)

            payload = {
                "intensity": intensity,
                "label": fn_label,
                "args_n": len(args),
                "kwargs_keys": list(kwargs.keys()),
            }
            eng.emit(event_name, payload, source="host")

            if heal:
                return eng.safe_call(fn, *args, default=default, label=fn_label, **kwargs)
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def on_event(event_name: str, engine: Any = None) -> Callable[[F], F]:
    """
    Decorator to subscribe a host function to bus events.

    Usage::

        @on_event("emergence")
        def celebrate(event):
            print(event.payload)
    """

    def decorator(fn: F) -> F:
        eng = engine or _DEFAULT_ENGINE
        if eng is not None:
            eng.bus.on(event_name, fn)
        else:
            # Lazy bind when engine attaches globals.
            _PENDING_SUBS.append((event_name, fn))
        return fn

    return decorator


_PENDING_SUBS: List[tuple] = []


def flush_pending_subscriptions(engine: Any) -> None:
    while _PENDING_SUBS:
        name, fn = _PENDING_SUBS.pop(0)
        engine.bus.on(name, fn)


class HostCallbackRegistry:
    """Reverse hooks: organism → host (e.g. request UI flash, play sound)."""

    def __init__(self) -> None:
        self._callbacks: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._callbacks[name] = fn

    def unregister(self, name: str) -> None:
        self._callbacks.pop(name, None)

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        fn = self._callbacks.get(name)
        if fn is None:
            return None
        return fn(*args, **kwargs)

    def names(self) -> List[str]:
        return list(self._callbacks.keys())


def host_callback(name: str, engine: Any = None) -> Callable[[F], F]:
    """
    Decorator to expose a host function to the organism.

    Usage::

        @host_callback("flash_screen")
        def flash(color=(255, 0, 0)):
            ...
    """

    def decorator(fn: F) -> F:
        eng = engine or _DEFAULT_ENGINE
        if eng is not None:
            eng.host_callbacks.register(name, fn)
        else:
            _PENDING_HOST.append((name, fn))
        return fn

    return decorator


_PENDING_HOST: List[tuple] = []


def flush_pending_host_callbacks(engine: Any) -> None:
    while _PENDING_HOST:
        name, fn = _PENDING_HOST.pop(0)
        engine.host_callbacks.register(name, fn)
