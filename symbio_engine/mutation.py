"""
Butterfly-effect mutation engine.

Tiny host signals cascade through the genome: a single click can shift
curiosity, which later unlocks creativity, which raises complexity, which
enables emergent modules. Amplification is intentional and bounded.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .events import Event
    from .organism import Organism


# Cascades: when gene A moves, gene B feels a fraction of that motion.
CASCADE_GRAPH: Dict[str, List[tuple]] = {
    "curiosity": [("creativity", 0.35), ("sensitivity", 0.15)],
    "sensitivity": [("empathy", 0.25), ("stress_proxy", 0.1)],
    "resilience": [("stability", 0.2), ("adaptability", -0.1)],
    "adaptability": [("curiosity", 0.15), ("creativity", 0.1)],
    "empathy": [("mood_proxy", 0.2), ("memory_depth", 0.1)],
    "creativity": [("curiosity", 0.12), ("stability", -0.08)],
    "stability": [("resilience", 0.1), ("adaptability", -0.12)],
    "memory_depth": [("empathy", 0.08), ("curiosity", 0.05)],
}


@dataclass
class MutationReport:
    primary: List[Dict[str, Any]] = field(default_factory=list)
    cascades: List[Dict[str, Any]] = field(default_factory=list)
    generation_bumped: bool = False
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary,
            "cascades": self.cascades,
            "generation_bumped": self.generation_bumped,
            "reason": self.reason,
        }


class MutationEngine:
    """Applies interaction-driven and ambient mutations with cascade effects."""

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self.total_mutations = 0
        self.last_report: Optional[MutationReport] = None

    def from_event(self, organism: "Organism", event: "Event") -> MutationReport:
        """Translate a host/runtime event into genome pressure."""
        name = event.name
        payload = event.payload
        intensity = float(payload.get("intensity", 0.35))
        tick = organism.age_ticks

        # Map common host signals → gene pressures.
        pressures: Dict[str, float] = {}
        if name in ("input", "click", "key", "player_action", "interaction"):
            pressures["curiosity"] = 0.02 * intensity
            pressures["sensitivity"] = 0.015 * intensity
            organism.register_interaction(str(payload.get("label", name)))
        elif name in ("error", "exception", "crash"):
            pressures["resilience"] = 0.03 * intensity
            pressures["stability"] = -0.01 * intensity
            pressures["adaptability"] = 0.025 * intensity
        elif name in ("success", "score", "reward", "win"):
            pressures["mood_proxy"] = 0.04 * intensity
            pressures["creativity"] = 0.02 * intensity
            pressures["curiosity"] = 0.01 * intensity
            organism.feel(0.05 * intensity, -0.02)
        elif name in ("idle", "boredom"):
            pressures["curiosity"] = 0.03 * intensity
            pressures["creativity"] = 0.02 * intensity
        elif name in ("damage", "hurt", "threat"):
            pressures["resilience"] = 0.04 * intensity
            pressures["sensitivity"] = 0.02 * intensity
            organism.feel(-0.04 * intensity, 0.06 * intensity)
        elif name in ("runtime_metric", "fps", "latency", "memory"):
            # Performance pressure: bad metrics raise adaptability.
            value = float(payload.get("value", 0.5))
            baseline = float(payload.get("baseline", 0.5))
            delta = (baseline - value)  # positive if worse than baseline for "higher is better"
            if payload.get("higher_is_better", True):
                delta = value - baseline
            # Prefer adaptability when metrics drift.
            pressures["adaptability"] = 0.01 * abs(delta)
            if delta < 0:
                pressures["stability"] = -0.01
                organism.feel(-0.01, 0.02)
        elif name == "tick":
            # Ambient drift — rare tiny mutations.
            if self.rng.random() < 0.08 * organism.genome.get("adaptability"):
                gene = self.rng.choice(list(organism.genome.genes.keys()))
                pressures[gene] = self.rng.uniform(-0.008, 0.008)
        else:
            # Generic stimulus.
            pressures["curiosity"] = 0.01 * intensity
            pressures["sensitivity"] = 0.008 * intensity
            organism.register_interaction(name)

        reason = f"event:{name}"
        return self.apply(organism, pressures, tick=tick, reason=reason)

    def apply(
        self,
        organism: "Organism",
        pressures: Dict[str, float],
        tick: int = 0,
        reason: str = "mutation",
        cascade_depth: int = 2,
    ) -> MutationReport:
        report = MutationReport(reason=reason)
        genome = organism.genome

        # Special non-gene proxies handled here.
        if "mood_proxy" in pressures:
            organism.feel(pressures.pop("mood_proxy"), 0.0)
        if "stress_proxy" in pressures:
            organism.feel(0.0, pressures.pop("stress_proxy"))

        for gene, delta in pressures.items():
            if gene not in genome.genes:
                # Organic feature growth: invent a new gene if creative enough.
                if genome.get("creativity") > 0.55 and self.rng.random() < 0.25:
                    genome.genes[gene] = genome._clamp(0.3 + delta)
                    genome.set_gene(gene, genome.genes[gene], tick=tick, reason=f"spawn:{reason}")
                    report.primary.append(
                        {"gene": gene, "delta": delta, "spawned": True}
                    )
                    self.total_mutations += 1
                continue

            before = genome.get(gene)
            after = genome.nudge(gene, delta, tick=tick, reason=reason)
            report.primary.append(
                {"gene": gene, "before": before, "after": after, "delta": after - before}
            )
            self.total_mutations += 1

            # Butterfly cascades.
            self._cascade(
                organism,
                gene,
                after - before,
                tick,
                reason,
                report,
                depth=cascade_depth,
            )

        # Complexity growth from any real change.
        if report.primary:
            genome.raise_complexity(0.02 * len(report.primary))
            # Occasional generation bump when enough pressure accumulates.
            if self.total_mutations % 12 == 0:
                genome.generation += 1
                report.generation_bumped = True
                organism.remember(
                    "generation",
                    f"Generation {genome.generation} — fingerprint {genome.fingerprint()}",
                    intensity=0.8,
                    tick=tick,
                )

        self.last_report = report
        return report

    def _cascade(
        self,
        organism: "Organism",
        source_gene: str,
        delta: float,
        tick: int,
        reason: str,
        report: MutationReport,
        depth: int,
    ) -> None:
        if depth <= 0 or abs(delta) < 1e-5:
            return
        genome = organism.genome
        edges = CASCADE_GRAPH.get(source_gene, [])
        for target, weight in edges:
            # Dampen by stability; amplify by sensitivity (butterfly).
            wing = (0.4 + genome.get("sensitivity")) * (1.1 - genome.get("stability") * 0.5)
            child_delta = delta * weight * wing * self.rng.uniform(0.7, 1.3)
            if target == "mood_proxy":
                organism.feel(child_delta, 0.0)
                report.cascades.append(
                    {"from": source_gene, "to": "mood", "delta": child_delta}
                )
                continue
            if target == "stress_proxy":
                organism.feel(0.0, abs(child_delta) * 0.5)
                report.cascades.append(
                    {"from": source_gene, "to": "stress", "delta": child_delta}
                )
                continue
            if target not in genome.genes:
                continue
            before = genome.get(target)
            after = genome.nudge(
                target,
                child_delta,
                tick=tick,
                reason=f"cascade:{source_gene}->{target}",
            )
            report.cascades.append(
                {
                    "from": source_gene,
                    "to": target,
                    "before": before,
                    "after": after,
                    "delta": after - before,
                }
            )
            self.total_mutations += 1
            # One more hop for true butterfly trails.
            self._cascade(
                organism,
                target,
                after - before,
                tick,
                reason,
                report,
                depth=depth - 1,
            )

    def forced_evolution(self, organism: "Organism", strength: float = 0.08) -> MutationReport:
        """Stronger evolutionary jolt used by the debugger after repeated failures."""
        genes = list(organism.genome.genes.keys())
        pressures = {
            g: self.rng.uniform(-strength, strength) for g in self.rng.sample(genes, k=min(3, len(genes)))
        }
        pressures["adaptability"] = pressures.get("adaptability", 0) + strength * 0.5
        pressures["resilience"] = pressures.get("resilience", 0) + strength * 0.4
        report = self.apply(
            organism,
            pressures,
            tick=organism.age_ticks,
            reason="forced_evolution",
            cascade_depth=3,
        )
        organism.genome.generation += 1
        report.generation_bumped = True
        return report

    @staticmethod
    def butterfly_index(organism: "Organism") -> float:
        """How 'chaotically sensitive' the organism currently is (0..1)."""
        g = organism.genome
        raw = g.get("sensitivity") * (1.0 - g.get("stability") * 0.6) * (0.5 + g.get("curiosity"))
        return max(0.0, min(1.0, raw))
