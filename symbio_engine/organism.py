"""Digital organism: vitality, mood, memory, and lifecycle state."""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from .genome import Genome


@dataclass
class Episode:
    """A short memory of something that happened to the organism."""

    kind: str
    summary: str
    intensity: float
    tick: int
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


@dataclass
class Organism:
    """
    Living state container.

    Starts minimal (low complexity, modest vitality) and deepens as the host
    feeds it events, errors, and runtime metrics.
    """

    name: str = "Wally"
    genome: Genome = field(default_factory=Genome)
    organism_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    born_at: float = field(default_factory=time.time)
    vitality: float = 0.72          # 0..1 life force
    stress: float = 0.10            # 0..1 damage / load
    mood: float = 0.55              # 0 sad .. 1 elated
    age_ticks: int = 0
    errors_seen: int = 0
    errors_healed: int = 0
    interactions: int = 0
    patches_applied: int = 0
    emergent_behaviors: List[str] = field(default_factory=list)
    memory: Deque[Episode] = field(default_factory=lambda: deque(maxlen=128))
    last_pulse: float = field(default_factory=time.time)
    alive: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)

    # --- lifecycle ---------------------------------------------------------

    def pulse(self, dt: float = 0.0) -> None:
        """Heartbeat: age, gently regulate stress/vitality."""
        self.age_ticks += 1
        self.last_pulse = time.time()
        # Natural stress decay scaled by resilience.
        decay = 0.01 + self.genome.get("resilience") * 0.04
        self.stress = max(0.0, self.stress - decay * max(dt, 0.05))
        # Vitality drifts toward equilibrium based on stress.
        target = max(0.15, 1.0 - self.stress * 0.7)
        self.vitality += (target - self.vitality) * 0.08
        self.vitality = max(0.05, min(1.0, self.vitality))
        # Mood slowly seeks mid-high if healthy.
        mood_target = 0.45 + self.vitality * 0.35 - self.stress * 0.25
        self.mood += (mood_target - self.mood) * 0.05
        self.mood = max(0.0, min(1.0, self.mood))
        if self.vitality < 0.08 and self.stress > 0.92:
            self.alive = False

    def remember(
        self,
        kind: str,
        summary: str,
        intensity: float = 0.3,
        tick: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Episode:
        depth = self.genome.get("memory_depth")
        # Higher memory_depth keeps more intensity in the summary weight.
        ep = Episode(
            kind=kind,
            summary=summary,
            intensity=min(1.0, intensity * (0.6 + depth)),
            tick=tick or self.age_ticks,
            tags=list(tags or []),
        )
        self.memory.append(ep)
        return ep

    def feel(self, delta_mood: float, delta_stress: float = 0.0) -> None:
        sens = self.genome.get("sensitivity")
        self.mood = max(0.0, min(1.0, self.mood + delta_mood * (0.5 + sens)))
        self.stress = max(0.0, min(1.0, self.stress + delta_stress * (0.5 + sens)))

    def register_interaction(self, label: str = "touch") -> None:
        self.interactions += 1
        self.feel(0.03, -0.01)
        self.remember("interaction", f"Host interaction: {label}", intensity=0.25)

    def register_error(self, message: str) -> None:
        self.errors_seen += 1
        self.feel(-0.08, 0.12)
        self.remember("error", message[:200], intensity=0.7, tags=["error"])

    def register_heal(self, message: str) -> None:
        self.errors_healed += 1
        self.feel(0.06, -0.1)
        self.remember("heal", message[:200], intensity=0.5, tags=["heal"])

    def register_patch(self, description: str) -> None:
        self.patches_applied += 1
        self.genome.raise_complexity(0.08)
        self.remember("patch", description[:200], intensity=0.55, tags=["patch"])

    def add_emergent(self, behavior: str) -> bool:
        if behavior not in self.emergent_behaviors:
            self.emergent_behaviors.append(behavior)
            self.genome.raise_complexity(0.25)
            self.remember("emergence", f"Awakened: {behavior}", intensity=0.9)
            return True
        return False

    @property
    def health(self) -> float:
        return max(0.0, min(1.0, self.vitality * (1.0 - self.stress * 0.5)))

    @property
    def lifespan_seconds(self) -> float:
        return max(0.0, time.time() - self.born_at)

    def status(self) -> Dict[str, Any]:
        return {
            "id": self.organism_id,
            "name": self.name,
            "alive": self.alive,
            "vitality": round(self.vitality, 3),
            "stress": round(self.stress, 3),
            "mood": round(self.mood, 3),
            "health": round(self.health, 3),
            "age_ticks": self.age_ticks,
            "lifespan_s": round(self.lifespan_seconds, 2),
            "interactions": self.interactions,
            "errors_seen": self.errors_seen,
            "errors_healed": self.errors_healed,
            "patches_applied": self.patches_applied,
            "emergent": list(self.emergent_behaviors),
            "genome": self.genome.snapshot(),
            "recent_memory": [
                {
                    "kind": e.kind,
                    "summary": e.summary,
                    "intensity": round(e.intensity, 3),
                    "tick": e.tick,
                }
                for e in list(self.memory)[-8:]
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "organism_id": self.organism_id,
            "born_at": self.born_at,
            "vitality": self.vitality,
            "stress": self.stress,
            "mood": self.mood,
            "age_ticks": self.age_ticks,
            "errors_seen": self.errors_seen,
            "errors_healed": self.errors_healed,
            "interactions": self.interactions,
            "patches_applied": self.patches_applied,
            "emergent_behaviors": list(self.emergent_behaviors),
            "alive": self.alive,
            "meta": dict(self.meta),
            "genome": self.genome.to_dict(),
            "memory": [
                {
                    "kind": e.kind,
                    "summary": e.summary,
                    "intensity": e.intensity,
                    "tick": e.tick,
                    "timestamp": e.timestamp,
                    "tags": list(e.tags),
                }
                for e in self.memory
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Organism":
        genome = Genome.from_dict(data.get("genome", {}))
        org = cls(
            name=data.get("name", "Wally"),
            genome=genome,
            organism_id=data.get("organism_id", uuid.uuid4().hex[:10]),
            born_at=float(data.get("born_at", time.time())),
            vitality=float(data.get("vitality", 0.72)),
            stress=float(data.get("stress", 0.1)),
            mood=float(data.get("mood", 0.55)),
            age_ticks=int(data.get("age_ticks", 0)),
            errors_seen=int(data.get("errors_seen", 0)),
            errors_healed=int(data.get("errors_healed", 0)),
            interactions=int(data.get("interactions", 0)),
            patches_applied=int(data.get("patches_applied", 0)),
            emergent_behaviors=list(data.get("emergent_behaviors", [])),
            alive=bool(data.get("alive", True)),
            meta=dict(data.get("meta", {})),
        )
        mem = deque(maxlen=128)
        for item in data.get("memory", []):
            mem.append(
                Episode(
                    kind=item.get("kind", "unknown"),
                    summary=item.get("summary", ""),
                    intensity=float(item.get("intensity", 0.3)),
                    tick=int(item.get("tick", 0)),
                    timestamp=float(item.get("timestamp", time.time())),
                    tags=list(item.get("tags", [])),
                )
            )
        org.memory = mem
        return org
