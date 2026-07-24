"""
Evolutionary self-debugger.

When the same failure pattern repeats, the debugger invents lightweight
"code patches" — strategy objects that alter future call behavior without
shipping arbitrary exec'd source (safe by design for a prototype).
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .organism import Organism
    from .mutation import MutationEngine


@dataclass
class Patch:
    """A living behavioral patch attached to a failure signature."""

    patch_id: str
    signature: str
    strategy: str
    description: str
    created_tick: int
    hits: int = 0
    successes: int = 0
    active: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)

    def score(self) -> float:
        if self.hits == 0:
            return 0.0
        return self.successes / self.hits


# Ordered catalog of evolutionary strategies the debugger can invent.
PATCH_STRATEGIES: List[str] = [
    "return_default",
    "clamp_numeric_args",
    "ignore_extra_kwargs",
    "retry_once",
    "swap_arg_order",
    "log_and_neutralize",
]


@dataclass
class DebugReport:
    signature: str
    action: str
    patch_id: Optional[str] = None
    detail: str = ""


class EvolutionaryDebugger:
    """
    Learns failure signatures and attaches patches that intercept future calls.

    This is intentionally *not* arbitrary code execution. Patches are pure
    strategy tokens applied by a sandbox interpreter — safe to embed in games.
    """

    def __init__(self) -> None:
        self.signatures: Dict[str, int] = defaultdict(int)
        self.patches: Dict[str, Patch] = {}
        self.signature_to_patch: Dict[str, str] = {}
        self._patch_counter = 0
        self.log: List[DebugReport] = []

    @staticmethod
    def signature_for(exc: BaseException, label: str = "") -> str:
        return f"{label}|{type(exc).__name__}|{str(exc)[:80]}"

    def observe_failure(
        self,
        exc: BaseException,
        *,
        label: str = "",
        organism: Optional["Organism"] = None,
        mutator: Optional["MutationEngine"] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DebugReport:
        sig = self.signature_for(exc, label)
        self.signatures[sig] += 1
        count = self.signatures[sig]

        # Escalate to a new patch when pattern is chronic.
        if count >= 2 and sig not in self.signature_to_patch:
            patch = self._invent_patch(sig, exc, organism)
            report = DebugReport(
                signature=sig,
                action="invent_patch",
                patch_id=patch.patch_id,
                detail=patch.description,
            )
            self.log.append(report)
            if organism is not None:
                organism.register_patch(patch.description)
                if mutator is not None:
                    mutator.apply(
                        organism,
                        {
                            "creativity": 0.03,
                            "adaptability": 0.025,
                            "resilience": 0.02,
                        },
                        tick=organism.age_ticks,
                        reason=f"patch:{patch.strategy}",
                    )
            return report

        if sig in self.signature_to_patch:
            return DebugReport(
                signature=sig,
                action="known_patch",
                patch_id=self.signature_to_patch[sig],
                detail="Existing patch will intercept future calls",
            )

        return DebugReport(
            signature=sig,
            action="observe",
            detail=f"Seen {count} time(s); patch after 2",
        )

    def _invent_patch(
        self,
        sig: str,
        exc: BaseException,
        organism: Optional["Organism"],
    ) -> Patch:
        self._patch_counter += 1
        etype = type(exc).__name__
        # Heuristic strategy selection from error class + creativity gene.
        creativity = organism.genome.get("creativity") if organism else 0.3
        if etype in (
            "KeyError",
            "IndexError",
            "AttributeError",
            "ZeroDivisionError",
            "RuntimeError",
            "NotImplementedError",
            "AssertionError",
        ):
            # Failures that rarely fix by arg surgery — neutralize safely.
            strategy = "return_default"
        elif etype in ("TypeError", "ValueError"):
            strategy = "clamp_numeric_args" if creativity < 0.5 else "ignore_extra_kwargs"
        elif etype in ("TimeoutError", "ConnectionError", "OSError"):
            strategy = "retry_once"
        else:
            # Prefer safe neutralization; creative organisms may try arg tricks.
            if creativity >= 0.55:
                idx = (self._patch_counter + int(creativity * 10)) % len(PATCH_STRATEGIES)
                strategy = PATCH_STRATEGIES[idx]
            else:
                strategy = "return_default"

        patch_id = f"P{self._patch_counter:04d}"
        desc = f"Patch {patch_id} [{strategy}] for {etype}: {str(exc)[:60]}"
        patch = Patch(
            patch_id=patch_id,
            signature=sig,
            strategy=strategy,
            description=desc,
            created_tick=organism.age_ticks if organism else 0,
            meta={"error_type": etype},
        )
        self.patches[patch_id] = patch
        self.signature_to_patch[sig] = patch_id
        return patch

    def apply_patch_if_any(
        self,
        *,
        fn: Callable[..., Any],
        args: tuple,
        kwargs: dict,
        label: str,
        default: Any = None,
        last_exc: Optional[BaseException] = None,
    ) -> Dict[str, Any]:
        """
        Try to run fn under an active patch for this label/error family.

        Returns dict with keys: handled (bool), result (Any), patch_id (str|None)
        """
        # Match any patch whose signature starts with this label.
        candidates = [
            p
            for p in self.patches.values()
            if p.active and p.signature.startswith(f"{label}|")
        ]
        if not candidates and last_exc is not None:
            sig = self.signature_for(last_exc, label)
            pid = self.signature_to_patch.get(sig)
            if pid:
                candidates = [self.patches[pid]]

        if not candidates:
            return {"handled": False, "result": None, "patch_id": None}

        # Prefer highest success score.
        candidates.sort(key=lambda p: p.score(), reverse=True)
        patch = candidates[0]
        patch.hits += 1
        try:
            result = self._execute_strategy(patch, fn, args, kwargs, default)
            patch.successes += 1
            return {"handled": True, "result": result, "patch_id": patch.patch_id}
        except Exception:
            return {"handled": False, "result": None, "patch_id": patch.patch_id}

    def _execute_strategy(
        self,
        patch: Patch,
        fn: Callable[..., Any],
        args: tuple,
        kwargs: dict,
        default: Any,
    ) -> Any:
        s = patch.strategy
        if s == "return_default":
            # Prefer a live success; only neutralize when the call still fails.
            # Otherwise a patch for one failure mode would block healthy paths
            # that share the same label (e.g. flaky(odd) after flaky(even)).
            try:
                return fn(*args, **kwargs)
            except Exception:
                return default
        if s == "clamp_numeric_args":
            new_args = []
            for a in args:
                if isinstance(a, (int, float)):
                    new_args.append(max(-1e6, min(1e6, a)) if a == a else 0)
                else:
                    new_args.append(a)
            new_kwargs = {
                k: (
                    max(-1e6, min(1e6, v))
                    if isinstance(v, (int, float)) and v == v
                    else v
                )
                for k, v in kwargs.items()
            }
            return fn(*tuple(new_args), **new_kwargs)
        if s == "ignore_extra_kwargs":
            try:
                return fn(*args, **kwargs)
            except TypeError:
                # Drop kwargs until it works (prototype-level).
                return fn(*args)
        if s == "retry_once":
            try:
                return fn(*args, **kwargs)
            except Exception:
                time.sleep(0.01)
                return fn(*args, **kwargs)
        if s == "swap_arg_order":
            if len(args) >= 2:
                swapped = (args[1], args[0]) + args[2:]
                return fn(*swapped, **kwargs)
            return fn(*args, **kwargs)
        if s == "log_and_neutralize":
            return default
        return default

    def evolve_callable(
        self,
        fn: Callable[..., Any],
        *,
        organism: "Organism",
        mutator: "MutationEngine",
        default: Any = None,
        label: str = "",
    ) -> Callable[..., Any]:
        """Return a callable that self-patches across repeated failures."""
        label = label or getattr(fn, "__name__", "fn")

        def evolved(*args: Any, **kwargs: Any) -> Any:
            # First try existing patches.
            patched = self.apply_patch_if_any(
                fn=fn, args=args, kwargs=kwargs, label=label, default=default
            )
            if patched["handled"]:
                return patched["result"]
            try:
                return fn(*args, **kwargs)
            except BaseException as exc:
                self.observe_failure(
                    exc,
                    label=label,
                    organism=organism,
                    mutator=mutator,
                    context={"args": args, "kwargs": kwargs},
                )
                # Immediate second chance with new patch.
                patched = self.apply_patch_if_any(
                    fn=fn,
                    args=args,
                    kwargs=kwargs,
                    label=label,
                    default=default,
                    last_exc=exc,
                )
                if patched["handled"]:
                    if organism is not None:
                        organism.register_heal(
                            f"Debugger patch {patched['patch_id']} handled {label}"
                        )
                    return patched["result"]
                raise

        evolved.__name__ = f"evolved_{label}"
        evolved.__symbio_label__ = label  # type: ignore[attr-defined]
        return evolved

    def stats(self) -> Dict[str, Any]:
        return {
            "signatures_tracked": len(self.signatures),
            "patches": [
                {
                    "id": p.patch_id,
                    "strategy": p.strategy,
                    "hits": p.hits,
                    "successes": p.successes,
                    "score": round(p.score(), 3),
                    "description": p.description,
                    "active": p.active,
                }
                for p in self.patches.values()
            ],
            "recent_log": [
                {
                    "signature": r.signature[:80],
                    "action": r.action,
                    "patch_id": r.patch_id,
                    "detail": r.detail,
                }
                for r in self.log[-10:]
            ],
        }
