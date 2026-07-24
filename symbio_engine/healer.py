"""
Self-healing layer.

Wraps risky host callbacks, classifies failures, applies recovery strategies,
and feeds outcomes back into the organism (stress down, resilience up).
"""

from __future__ import annotations

import functools
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .organism import Organism
    from .mutation import MutationEngine

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class HealRecord:
    error_type: str
    message: str
    strategy: str
    success: bool
    tick: int
    timestamp: float = field(default_factory=time.time)


class SelfHealer:
    """
    Strategies (in order of preference for known error classes):

    - retry: re-invoke with short backoff
    - default: return a safe default
    - skip: swallow and continue
    - coerce: type-coerce common argument mistakes
    - evolve: hand off to evolutionary debugger for a patch
    """

    STRATEGY_TABLE: Dict[str, List[str]] = {
        "ZeroDivisionError": ["default", "skip"],
        "KeyError": ["default", "skip"],
        "IndexError": ["default", "skip"],
        "TypeError": ["coerce", "default", "retry"],
        "ValueError": ["coerce", "default", "retry"],
        "AttributeError": ["default", "skip", "evolve"],
        "TimeoutError": ["retry", "skip"],
        "ConnectionError": ["retry", "skip"],
        "RuntimeError": ["retry", "default", "evolve"],
        "*": ["retry", "default", "skip", "evolve"],
    }

    def __init__(self, max_retries: int = 2) -> None:
        self.max_retries = max_retries
        self.history: Deque[HealRecord] = deque(maxlen=200)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.success_counts: Dict[str, int] = defaultdict(int)

    def wrap(
        self,
        fn: F,
        *,
        organism: Optional["Organism"] = None,
        mutator: Optional["MutationEngine"] = None,
        default: Any = None,
        on_evolve: Optional[Callable[[BaseException, Dict[str, Any]], Any]] = None,
        label: str = "",
    ) -> F:
        """Return a self-healing proxy around ``fn``."""

        @functools.wraps(fn)
        def guarded(*args: Any, **kwargs: Any) -> Any:
            return self.run(
                fn,
                args=args,
                kwargs=kwargs,
                organism=organism,
                mutator=mutator,
                default=default,
                on_evolve=on_evolve,
                label=label or getattr(fn, "__name__", "callable"),
            )

        return guarded  # type: ignore[return-value]

    def run(
        self,
        fn: Callable[..., Any],
        *,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        organism: Optional["Organism"] = None,
        mutator: Optional["MutationEngine"] = None,
        default: Any = None,
        on_evolve: Optional[Callable[[BaseException, Dict[str, Any]], Any]] = None,
        label: str = "callable",
    ) -> Any:
        kwargs = kwargs or {}
        last_exc: Optional[BaseException] = None
        context: Dict[str, Any] = {
            "label": label,
            "args": args,
            "kwargs": kwargs,
            "default": default,
        }

        try:
            return fn(*args, **kwargs)
        except BaseException as exc:
            last_exc = exc
            if organism is not None:
                organism.register_error(f"{type(exc).__name__} in {label}: {exc}")

        assert last_exc is not None
        etype = type(last_exc).__name__
        self.error_counts[etype] += 1
        strategies = list(self.STRATEGY_TABLE.get(etype, self.STRATEGY_TABLE["*"]))

        # Prefer evolve when this error class is chronic.
        if self.error_counts[etype] >= 3 and "evolve" not in strategies[:1]:
            strategies = ["evolve"] + [s for s in strategies if s != "evolve"]

        tick = organism.age_ticks if organism else 0

        for strategy in strategies:
            try:
                result = self._apply_strategy(
                    strategy,
                    fn=fn,
                    exc=last_exc,
                    context=context,
                    default=default,
                    on_evolve=on_evolve,
                    organism=organism,
                    mutator=mutator,
                )
                self.history.append(
                    HealRecord(
                        error_type=etype,
                        message=str(last_exc),
                        strategy=strategy,
                        success=True,
                        tick=tick,
                    )
                )
                self.success_counts[strategy] += 1
                if organism is not None:
                    organism.register_heal(
                        f"Healed {etype} via {strategy} in {label}"
                    )
                    if mutator is not None:
                        mutator.apply(
                            organism,
                            {"resilience": 0.02, "adaptability": 0.015},
                            tick=tick,
                            reason=f"heal:{strategy}",
                        )
                return result
            except Exception:
                self.history.append(
                    HealRecord(
                        error_type=etype,
                        message=str(last_exc),
                        strategy=strategy,
                        success=False,
                        tick=tick,
                    )
                )
                continue

        # All strategies failed — re-raise original after recording.
        if organism is not None:
            organism.feel(-0.05, 0.08)
            organism.remember(
                "unhealed",
                f"Could not heal {etype} in {label}",
                intensity=0.85,
                tags=["error", "critical"],
            )
        raise last_exc

    def _apply_strategy(
        self,
        strategy: str,
        *,
        fn: Callable[..., Any],
        exc: BaseException,
        context: Dict[str, Any],
        default: Any,
        on_evolve: Optional[Callable[[BaseException, Dict[str, Any]], Any]],
        organism: Optional["Organism"],
        mutator: Optional["MutationEngine"],
    ) -> Any:
        if strategy == "retry":
            delay = 0.01
            last: Optional[BaseException] = None
            for attempt in range(self.max_retries):
                try:
                    time.sleep(delay * (attempt + 1))
                    return fn(*context["args"], **context["kwargs"])
                except BaseException as e:
                    last = e
            if last:
                raise last
            raise exc

        if strategy == "default":
            return default

        if strategy == "skip":
            return default

        if strategy == "coerce":
            # Best-effort: stringify / int-cast simple kwargs and retry once.
            new_kwargs = dict(context["kwargs"])
            for k, v in list(new_kwargs.items()):
                if isinstance(v, str) and v.isdigit():
                    new_kwargs[k] = int(v)
                elif isinstance(v, float) and v.is_integer():
                    new_kwargs[k] = int(v)
            new_args = []
            for a in context["args"]:
                if isinstance(a, str) and a.isdigit():
                    new_args.append(int(a))
                else:
                    new_args.append(a)
            return fn(*tuple(new_args), **new_kwargs)

        if strategy == "evolve":
            if on_evolve is not None:
                return on_evolve(exc, context)
            if mutator is not None and organism is not None:
                mutator.forced_evolution(organism, strength=0.06)
            return default

        raise RuntimeError(f"Unknown heal strategy: {strategy}")

    def stats(self) -> Dict[str, Any]:
        return {
            "error_counts": dict(self.error_counts),
            "success_counts": dict(self.success_counts),
            "recent": [
                {
                    "error_type": r.error_type,
                    "strategy": r.strategy,
                    "success": r.success,
                    "message": r.message[:120],
                    "tick": r.tick,
                }
                for r in list(self.history)[-10:]
            ],
        }

    def format_traceback(self, exc: BaseException) -> str:
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
