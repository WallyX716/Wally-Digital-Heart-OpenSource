"""
2041-style emergent behavior layer.

As complexity, genes, and lived experience cross thresholds, new modules
"awaken" — not scripted cutscenes, but organic unlocks that change how the
organism responds to the host.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .organism import Organism
    from .events import Event, EventBus


@dataclass
class EmergentModule:
    name: str
    title: str
    description: str
    # All conditions must pass.
    min_complexity: float = 1.5
    min_generation: int = 0
    min_interactions: int = 0
    min_gene: Dict[str, float] = field(default_factory=dict)
    requires: List[str] = field(default_factory=list)
    on_awaken: Optional[Callable[["Organism"], None]] = None
    on_tick: Optional[Callable[["Organism", float], None]] = None
    on_event: Optional[Callable[["Organism", "Event"], None]] = None


def _mod_echo_chamber(org: "Organism") -> None:
    org.meta["echo_gain"] = 0.15 + org.genome.get("empathy") * 0.3


def _mod_echo_event(org: "Organism", event: "Event") -> None:
    # Mirrors host emotional valence back as mood shimmer.
    valence = float(event.payload.get("valence", 0.0))
    if valence:
        gain = float(org.meta.get("echo_gain", 0.2))
        org.feel(valence * gain, 0.0)


def _mod_dream_awaken(org: "Organism") -> None:
    org.meta["dreaming"] = False
    org.meta["dream_buffer"] = []


def _mod_dream_tick(org: "Organism", dt: float) -> None:
    # Idle → dream: recombine memories into synthetic episodes.
    if org.meta.get("last_interaction_gap", 0) > 3.0:
        org.meta["dreaming"] = True
        if org.memory and org.age_ticks % 15 == 0:
            pieces = list(org.memory)[-5:]
            if len(pieces) >= 2:
                dream = f"Dream-weave: {pieces[0].kind} ⊕ {pieces[-1].kind}"
                org.remember("dream", dream, intensity=0.4, tags=["dream", "2041"])
                org.genome.nudge("creativity", 0.005, tick=org.age_ticks, reason="dream")
    else:
        org.meta["dreaming"] = False


def _mod_prophet_awaken(org: "Organism") -> None:
    org.meta["predictions"] = []


def _mod_prophet_event(org: "Organism", event: "Event") -> None:
    # Naive next-event prophecy based on recent history patterns.
    hist = org.meta.setdefault("event_name_hist", [])
    hist.append(event.name)
    if len(hist) > 40:
        del hist[:-40]
    if len(hist) < 4:
        return
    # Predict most common successor of last event.
    last = hist[-2] if len(hist) >= 2 else event.name
    successors: Dict[str, int] = {}
    for i in range(len(hist) - 1):
        if hist[i] == last:
            nxt = hist[i + 1]
            successors[nxt] = successors.get(nxt, 0) + 1
    if successors:
        prediction = max(successors, key=successors.get)  # type: ignore[arg-type]
        org.meta["predictions"] = (org.meta.get("predictions") or [])[-9:] + [
            {"given": last, "predicts": prediction, "tick": org.age_ticks}
        ]


def _mod_immune_awaken(org: "Organism") -> None:
    org.meta["immune_threshold"] = 0.55


def _mod_immune_tick(org: "Organism", dt: float) -> None:
    # Auto-soothe when stress spikes past threshold.
    thr = float(org.meta.get("immune_threshold", 0.55))
    if org.stress > thr:
        soothe = 0.02 + org.genome.get("resilience") * 0.05
        org.stress = max(0.0, org.stress - soothe)
        if org.age_ticks % 20 == 0:
            org.remember("immune", "Autonomic stress purge", intensity=0.35, tags=["immune"])


def _mod_symbiote_awaken(org: "Organism") -> None:
    org.meta["symbiosis"] = 0.1


def _mod_symbiote_event(org: "Organism", event: "Event") -> None:
    if event.source == "host":
        org.meta["symbiosis"] = min(
            1.0, float(org.meta.get("symbiosis", 0.1)) + 0.01
        )
        # Host and organism mood begin to co-regulate.
        host_mood = event.payload.get("host_mood")
        if host_mood is not None:
            target = float(host_mood)
            org.mood += (target - org.mood) * (0.05 + org.genome.get("empathy") * 0.1)


def _mod_polyphony_awaken(org: "Organism") -> None:
    org.meta["voices"] = ["core"]


def _mod_polyphony_tick(org: "Organism", dt: float) -> None:
    # Multiple internal "voices" comment on state — surface as memories.
    if org.age_ticks % 25 != 0:
        return
    voices = []
    if org.genome.get("curiosity") > 0.5:
        voices.append("seeker")
    if org.genome.get("resilience") > 0.5:
        voices.append("guardian")
    if org.genome.get("creativity") > 0.45:
        voices.append("poet")
    if org.stress > 0.5:
        voices.append("alarm")
    org.meta["voices"] = voices or ["core"]
    if len(voices) >= 2:
        org.remember(
            "polyphony",
            f"Inner council: {', '.join(voices)}",
            intensity=0.3,
            tags=["2041", "polyphony"],
        )


def _mod_chronos_awaken(org: "Organism") -> None:
    org.meta["tempo"] = 1.0


def _mod_chronos_tick(org: "Organism", dt: float) -> None:
    # Subjective time dilates under high curiosity or stress.
    c = org.genome.get("curiosity")
    s = org.stress
    tempo = 1.0 + (c - 0.4) * 0.5 + s * 0.3
    org.meta["tempo"] = max(0.5, min(2.0, tempo))


# Catalog of awakenable modules (2041 palette).
EMERGENT_CATALOG: List[EmergentModule] = [
    EmergentModule(
        name="echo_chamber",
        title="Echo Chamber",
        description="Mirrors host emotional valence; early symbiotic feedback.",
        min_complexity=1.8,
        min_interactions=3,
        min_gene={"empathy": 0.28},
        on_awaken=_mod_echo_chamber,
        on_event=_mod_echo_event,
    ),
    EmergentModule(
        name="dream_weaver",
        title="Dream Weaver",
        description="During idle gaps, recombines memories into creative dreams.",
        min_complexity=2.5,
        min_generation=1,
        min_gene={"creativity": 0.22, "memory_depth": 0.28},
        on_awaken=_mod_dream_awaken,
        on_tick=_mod_dream_tick,
    ),
    EmergentModule(
        name="pattern_prophet",
        title="Pattern Prophet",
        description="Forecasts likely next host events from lived sequences.",
        min_complexity=3.2,
        min_interactions=8,
        min_gene={"curiosity": 0.4, "memory_depth": 0.3},
        requires=["echo_chamber"],
        on_awaken=_mod_prophet_awaken,
        on_event=_mod_prophet_event,
    ),
    EmergentModule(
        name="immune_reflex",
        title="Immune Reflex",
        description="Autonomic stress purge when load exceeds threshold.",
        min_complexity=2.2,
        min_gene={"resilience": 0.4},
        on_awaken=_mod_immune_awaken,
        on_tick=_mod_immune_tick,
    ),
    EmergentModule(
        name="true_symbiote",
        title="True Symbiote",
        description="Deep host co-regulation — 2041 bond meter comes online.",
        min_complexity=4.0,
        min_generation=2,
        min_interactions=15,
        min_gene={"empathy": 0.4, "sensitivity": 0.35},
        requires=["echo_chamber", "immune_reflex"],
        on_awaken=_mod_symbiote_awaken,
        on_event=_mod_symbiote_event,
    ),
    EmergentModule(
        name="inner_polyphony",
        title="Inner Polyphony",
        description="Multiple internal voices debate state; narrative richness.",
        min_complexity=5.0,
        min_generation=3,
        min_gene={"creativity": 0.35, "curiosity": 0.45},
        requires=["dream_weaver"],
        on_awaken=_mod_polyphony_awaken,
        on_tick=_mod_polyphony_tick,
    ),
    EmergentModule(
        name="chronos_sense",
        title="Chronos Sense",
        description="Subjective tempo warps with curiosity and stress.",
        min_complexity=3.5,
        min_gene={"sensitivity": 0.4, "adaptability": 0.35},
        on_awaken=_mod_chronos_awaken,
        on_tick=_mod_chronos_tick,
    ),
]


class EmergenceController:
    """Evaluates thresholds and runs active emergent modules."""

    def __init__(self, catalog: Optional[List[EmergentModule]] = None) -> None:
        self.catalog = list(catalog or EMERGENT_CATALOG)
        self.active: Dict[str, EmergentModule] = {}
        self.awaken_log: List[Dict[str, Any]] = []

    def restore_from_organism(self, organism: "Organism") -> List[str]:
        """
        Re-bind previously unlocked modules after a state load.

        Does **not** re-run ``on_awaken`` so persisted meta (bond meters,
        dream buffers, tempos, etc.) is preserved across sessions.
        """
        restored: List[str] = []
        known = set(organism.emergent_behaviors) | {
            m for m in organism.genome.unlocked_modules if m != "core"
        }
        by_name = {m.name: m for m in self.catalog}
        for name in known:
            mod = by_name.get(name)
            if mod is None or name in self.active:
                continue
            self.active[name] = mod
            restored.append(name)
        return restored

    def evaluate(self, organism: "Organism") -> List[str]:
        newly: List[str] = []
        unlocked = set(organism.genome.unlocked_modules) | set(self.active.keys())
        for mod in self.catalog:
            if mod.name in self.active:
                continue
            if not self._eligible(mod, organism, unlocked):
                continue
            self.active[mod.name] = mod
            organism.genome.unlock(mod.name)
            organism.add_emergent(mod.name)
            if mod.on_awaken:
                try:
                    mod.on_awaken(organism)
                except Exception:
                    pass
            entry = {
                "name": mod.name,
                "title": mod.title,
                "tick": organism.age_ticks,
                "complexity": organism.genome.complexity,
            }
            self.awaken_log.append(entry)
            newly.append(mod.name)
            unlocked.add(mod.name)
        return newly

    def _eligible(
        self,
        mod: EmergentModule,
        organism: "Organism",
        unlocked: set,
    ) -> bool:
        g = organism.genome
        if g.complexity < mod.min_complexity:
            return False
        if g.generation < mod.min_generation:
            return False
        if organism.interactions < mod.min_interactions:
            return False
        for gene, need in mod.min_gene.items():
            if g.get(gene) < need:
                return False
        for req in mod.requires:
            if req not in unlocked and req not in organism.emergent_behaviors:
                return False
        return True

    def tick(self, organism: "Organism", dt: float) -> None:
        for mod in self.active.values():
            if mod.on_tick:
                try:
                    mod.on_tick(organism, dt)
                except Exception:
                    pass

    def on_event(self, organism: "Organism", event: "Event") -> None:
        for mod in self.active.values():
            if mod.on_event:
                try:
                    mod.on_event(organism, event)
                except Exception:
                    pass

    def status(self) -> Dict[str, Any]:
        return {
            "active": [
                {"name": m.name, "title": m.title, "description": m.description}
                for m in self.active.values()
            ],
            "available_catalog": [
                {
                    "name": m.name,
                    "title": m.title,
                    "min_complexity": m.min_complexity,
                    "requires": list(m.requires),
                }
                for m in self.catalog
            ],
            "awaken_log": list(self.awaken_log[-12:]),
        }
