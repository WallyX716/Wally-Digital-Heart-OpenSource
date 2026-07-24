"""
SymbioEngine — the public façade.

Drop into any Python program::

    from symbio_engine import SymbioEngine

    engine = SymbioEngine(name="Wally")
    engine.boot()

    @engine.hook("player_jump")
    def jump():
        ...

    engine.pulse()          # once per frame / tick
    print(engine.status())
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .debugger import EvolutionaryDebugger
from .emergence import EmergenceController
from .events import Event, EventBus
from .genome import Genome
from .healer import SelfHealer
from .hooks import (
    HostCallbackRegistry,
    flush_pending_host_callbacks,
    flush_pending_subscriptions,
    set_default_engine,
    symbio_hook,
)
from .mutation import MutationEngine
from .organism import Organism
from .persistence import Persistence
from .sensors import SensorSuite

F = TypeVar("F", bound=Callable[..., Any])


class SymbioEngine:
    """
    Living digital organism wrapper.

    Lifecycle:
      1. Construct with optional name/seed/state path.
      2. ``boot()`` (or rely on lazy boot on first pulse).
      3. Feed events via ``emit`` / hooks / ``observe``.
      4. Call ``pulse(dt)`` each frame or on a timer.
      5. ``shutdown()`` to persist and detach.
    """

    def __init__(
        self,
        name: str = "Wally",
        *,
        seed: Optional[int] = None,
        state_path: Optional[str] = None,
        auto_save: bool = True,
        auto_load: bool = True,
    ) -> None:
        self.seed = seed if seed is not None else random.randint(1, 2**31 - 1)
        self.rng = random.Random(self.seed)
        self.bus = EventBus()
        self.organism = Organism(name=name, genome=Genome(seed=self.seed))
        self.mutator = MutationEngine(rng=self.rng)
        self.healer = SelfHealer()
        self.debugger = EvolutionaryDebugger()
        self.sensors = SensorSuite()
        self.emergence = EmergenceController()
        self.host_callbacks = HostCallbackRegistry()
        self.persistence = Persistence(state_path)
        self.auto_save = auto_save
        self.auto_load = auto_load
        self._booted = False
        self._last_pulse = time.time()
        self._last_interaction_at = time.time()
        self._pulse_count = 0
        self._save_every_pulses = 50
        self._listeners_bound = False

    # ------------------------------------------------------------------ boot

    def boot(self, force_fresh: bool = False) -> "SymbioEngine":
        """Initialize, optionally restore from disk, bind internal listeners."""
        if self._booted and not force_fresh:
            return self

        if self.auto_load and not force_fresh and self.persistence.exists():
            data = self.persistence.load()
            if data and "organism" in data:
                self.organism = Organism.from_dict(data["organism"])
                dbg = data.get("debugger")
                if dbg:
                    self._restore_debugger(dbg)
                # Re-bind emergent modules without re-running on_awaken
                # so persisted meta (symbiosis, dreams, tempo, …) survives.
                self.emergence.restore_from_organism(self.organism)
                extra = data.get("extra") or {}
                if "pulses" in extra:
                    try:
                        self._pulse_count = int(extra["pulses"])
                    except (TypeError, ValueError):
                        pass
                if "seed" in extra and extra["seed"] is not None:
                    try:
                        self.seed = int(extra["seed"])
                        self.rng = random.Random(self.seed)
                        self.mutator.rng = self.rng
                    except (TypeError, ValueError):
                        pass

        self._bind_internal()
        set_default_engine(self)
        flush_pending_subscriptions(self)
        flush_pending_host_callbacks(self)
        self._booted = True
        self.bus.emit(
            "boot",
            {
                "name": self.organism.name,
                "id": self.organism.organism_id,
                "generation": self.organism.genome.generation,
                "complexity": self.organism.genome.complexity,
                "emergent": list(self.organism.emergent_behaviors),
            },
            source="organism",
        )
        self.organism.remember("boot", "SymbioEngine online", intensity=0.5)
        return self

    def _restore_debugger(self, dbg: Dict[str, Any]) -> None:
        from .debugger import Patch

        self.debugger.signatures.update(
            {k: int(v) for k, v in dbg.get("signatures", {}).items()}
        )
        for pid, raw in dbg.get("patches", {}).items():
            self.debugger.patches[pid] = Patch(
                patch_id=raw["patch_id"],
                signature=raw["signature"],
                strategy=raw["strategy"],
                description=raw["description"],
                created_tick=int(raw.get("created_tick", 0)),
                hits=int(raw.get("hits", 0)),
                successes=int(raw.get("successes", 0)),
                active=bool(raw.get("active", True)),
                meta=dict(raw.get("meta", {})),
            )
        self.debugger.signature_to_patch.update(dbg.get("signature_to_patch", {}))
        self.debugger._patch_counter = int(dbg.get("_patch_counter", 0))

    def _bind_internal(self) -> None:
        if self._listeners_bound:
            return
        self._listeners_bound = True

        def _on_any(event: Event) -> None:
            # Skip pure lifecycle / meta chatter (emergence is broadcast-only).
            if event.name in ("pulse", "status", "boot", "shutdown", "emergence"):
                return

            # Mutations only from host / sensor / explicit organism tick.
            if event.source in ("host", "sensor") or event.name == "tick":
                self.mutator.from_event(self.organism, event)
                if event.source == "host":
                    self._last_interaction_at = time.time()

            if event.source in ("host", "sensor"):
                self.emergence.on_event(self.organism, event)
                newly = self.emergence.evaluate(self.organism)
                for name in newly:
                    self.bus.emit(
                        "emergence",
                        {
                            "module": name,
                            "title": self.emergence.active[name].title,
                            "description": self.emergence.active[name].description,
                        },
                        source="organism",
                    )
                    # Notify host if they registered a callback.
                    self.host_callbacks.call(
                        "on_emergence",
                        name,
                        self.emergence.active[name].title,
                    )

        self.bus.on("*", _on_any)

    def attach_globals(self) -> "SymbioEngine":
        """Make this engine the default for ``@symbio_hook`` decorators."""
        if not self._booted:
            self.boot()
        set_default_engine(self)
        flush_pending_subscriptions(self)
        flush_pending_host_callbacks(self)
        return self

    # ------------------------------------------------------------------ pulse

    def pulse(self, dt: Optional[float] = None) -> Dict[str, Any]:
        """
        Heartbeat. Call once per game frame or on a schedule.

        Advances age, ambient mutation, sensors, emergence, optional autosave.
        """
        if not self._booted:
            self.boot()

        now = time.time()
        if dt is None:
            dt = max(0.0, now - self._last_pulse)
        self._last_pulse = now
        self._pulse_count += 1

        org = self.organism
        if not org.alive:
            return {"alive": False, "message": "Organism is dormant"}

        org.meta["last_interaction_gap"] = now - self._last_interaction_at
        org.pulse(dt)

        # Ambient tick event (rare mutations).
        self.mutator.from_event(
            org,
            Event(name="tick", payload={"dt": dt, "intensity": 0.1}, source="organism"),
        )

        # Sensors every few pulses to stay light.
        if self._pulse_count % 10 == 0:
            for ev in self.sensors.as_mutation_events():
                self.mutator.from_event(
                    org,
                    Event(
                        name=ev["name"],
                        payload=ev["payload"],
                        source="sensor",
                    ),
                )

        self.emergence.tick(org, dt)
        newly = self.emergence.evaluate(org)
        for name in newly:
            self.bus.emit(
                "emergence",
                {
                    "module": name,
                    "title": self.emergence.active[name].title,
                    "description": self.emergence.active[name].description,
                },
                source="organism",
            )

        self.bus.emit(
            "pulse",
            {
                "dt": dt,
                "tick": org.age_ticks,
                "health": org.health,
                "mood": org.mood,
            },
            source="organism",
        )

        if self.auto_save and self._pulse_count % self._save_every_pulses == 0:
            self.save()

        return {
            "alive": org.alive,
            "tick": org.age_ticks,
            "health": round(org.health, 3),
            "mood": round(org.mood, 3),
            "complexity": round(org.genome.complexity, 3),
            "generation": org.genome.generation,
            "emergent": list(org.emergent_behaviors),
            "butterfly": round(self.mutator.butterfly_index(org), 3),
        }

    # ------------------------------------------------------------------ I/O

    def emit(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "host",
    ) -> Event:
        if not self._booted:
            self.boot()
        return self.bus.emit(name, payload, source=source)

    def observe(self, name: str, **payload: Any) -> Event:
        """Shorthand for host observations (fps, score, damage, etc.)."""
        return self.emit(name, payload, source="host")

    def interact(self, label: str = "touch", intensity: float = 0.4, **extra: Any) -> Event:
        data = {"label": label, "intensity": intensity}
        data.update(extra)
        return self.emit("interaction", data, source="host")

    def push_metric(self, name: str, value: float, unit: str = "") -> None:
        self.sensors.push(name, value, unit=unit)

    # ------------------------------------------------------------------ safety

    def safe_call(
        self,
        fn: Callable[..., Any],
        *args: Any,
        default: Any = None,
        label: str = "",
        **kwargs: Any,
    ) -> Any:
        """Run ``fn`` with self-healing + evolutionary patches."""
        if not self._booted:
            self.boot()
        label = label or getattr(fn, "__name__", "callable")

        def on_evolve(exc: BaseException, context: Dict[str, Any]) -> Any:
            self.debugger.observe_failure(
                exc,
                label=label,
                organism=self.organism,
                mutator=self.mutator,
                context=context,
            )
            patched = self.debugger.apply_patch_if_any(
                fn=fn,
                args=context.get("args", ()),
                kwargs=context.get("kwargs", {}),
                label=label,
                default=default,
                last_exc=exc,
            )
            if patched["handled"]:
                return patched["result"]
            return default

        # Prefer existing patch before raw healer path. Strategies such as
        # return_default try the live callable first, then neutralize.
        pre = self.debugger.apply_patch_if_any(
            fn=fn, args=args, kwargs=kwargs, label=label, default=default
        )
        if pre["handled"] and pre["patch_id"]:
            patch = self.debugger.patches.get(pre["patch_id"])
            if patch is not None and patch.active:
                return pre["result"]

        return self.healer.run(
            fn,
            args=args,
            kwargs=kwargs,
            organism=self.organism,
            mutator=self.mutator,
            default=default,
            on_evolve=on_evolve,
            label=label,
        )

    def evolve(self, fn: Callable[..., Any], *, default: Any = None, label: str = "") -> Callable[..., Any]:
        """Return an evolution-wrapped callable (self-debugging over time)."""
        if not self._booted:
            self.boot()
        return self.debugger.evolve_callable(
            fn,
            organism=self.organism,
            mutator=self.mutator,
            default=default,
            label=label or getattr(fn, "__name__", "fn"),
        )

    def hook(
        self,
        event_name: str = "interaction",
        *,
        intensity: float = 0.4,
        heal: bool = True,
        default: Any = None,
        label: str = "",
    ) -> Callable[[F], F]:
        """Instance-bound version of ``@symbio_hook``."""
        if not self._booted:
            self.boot()
        return symbio_hook(
            event_name,
            intensity=intensity,
            heal=heal,
            default=default,
            engine=self,
            label=label,
        )

    def on(self, event_name: str, handler: Callable[[Event], None]) -> Callable[[], None]:
        if not self._booted:
            self.boot()
        return self.bus.on(event_name, handler)

    def register_host(self, name: str, fn: Callable[..., Any]) -> None:
        self.host_callbacks.register(name, fn)

    def ask_host(self, name: str, *args: Any, **kwargs: Any) -> Any:
        return self.host_callbacks.call(name, *args, **kwargs)

    # ------------------------------------------------------------------ status

    def status(self) -> Dict[str, Any]:
        if not self._booted:
            self.boot()
        # Prefer a portable relative path in status (no host-specific absolute paths).
        state_display = str(self.persistence.path)
        try:
            state_display = os.path.relpath(self.persistence.path)
        except (ValueError, TypeError):
            pass

        return {
            "engine": {
                "booted": self._booted,
                "seed": self.seed,
                "pulses": self._pulse_count,
                "auto_save": self.auto_save,
                "state_path": state_display,
            },
            "organism": self.organism.status(),
            "butterfly_index": round(self.mutator.butterfly_index(self.organism), 3),
            "mutations": self.mutator.total_mutations,
            "healer": self.healer.stats(),
            "debugger": self.debugger.stats(),
            "emergence": self.emergence.status(),
            "sensors": self.sensors.snapshot(),
            "host_callbacks": self.host_callbacks.names(),
        }

    def narrative(self) -> str:
        """Human-readable snapshot — great for debug HUDs or consoles."""
        if not self._booted:
            self.boot()
        o = self.organism
        g = o.genome
        lines = [
            f"═══ {o.name} [{o.organism_id}] ═══",
            f"Alive: {o.alive}  Health: {o.health:.2f}  Mood: {o.mood:.2f}  Stress: {o.stress:.2f}",
            f"Gen {g.generation}  Complexity {g.complexity:.2f}  Fingerprint {g.fingerprint()}",
            f"Butterfly index: {self.mutator.butterfly_index(o):.2f}",
            f"Interactions: {o.interactions}  Healed: {o.errors_healed}/{o.errors_seen}  Patches: {o.patches_applied}",
            f"Modules: {', '.join(g.unlocked_modules)}",
            f"Emergent: {', '.join(o.emergent_behaviors) or '(latent)'}",
            "Genes: "
            + ", ".join(f"{k}={v:.2f}" for k, v in sorted(g.genes.items())),
        ]
        if o.memory:
            lines.append("Recent memory:")
            for ep in list(o.memory)[-5:]:
                lines.append(f"  • [{ep.kind}] {ep.summary}")
        if self.emergence.active:
            lines.append("Awakened behaviors:")
            for m in self.emergence.active.values():
                lines.append(f"  ✦ {m.title}: {m.description}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ persist

    def save(self) -> str:
        return self.persistence.save(
            self.organism,
            extra={"seed": self.seed, "pulses": self._pulse_count},
            debugger=self.debugger,
        )

    def shutdown(self) -> None:
        if self._booted and self.auto_save:
            self.save()
        self.bus.emit("shutdown", {"name": self.organism.name}, source="organism")
        self._booted = False

    # ------------------------------------------------------------------ repr

    def __repr__(self) -> str:
        o = self.organism
        return (
            f"<SymbioEngine name={o.name!r} gen={o.genome.generation} "
            f"complexity={o.genome.complexity:.2f} alive={o.alive}>"
        )
