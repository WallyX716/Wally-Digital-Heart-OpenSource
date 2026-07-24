"""Genome: trait genes that start minimal and mutate over lifetime."""

from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Baseline starter genes — deliberately tiny. Complexity grows later.
DEFAULT_GENES: Dict[str, float] = {
    "resilience": 0.35,       # recovery from errors
    "curiosity": 0.40,        # appetite for new stimuli
    "sensitivity": 0.30,      # how hard small inputs hit (butterfly lever)
    "adaptability": 0.35,     # how fast traits drift under pressure
    "memory_depth": 0.25,     # how long episodes linger
    "empathy": 0.20,          # host-signal mirroring (2041 symbiosis)
    "creativity": 0.15,       # chance of inventive emergent modules
    "stability": 0.55,        # resistance to chaotic mutation
}

# Soft bounds so the organism never collapses into noise.
GENE_MIN = 0.01
GENE_MAX = 0.99


@dataclass
class GeneLogEntry:
    tick: int
    gene: str
    before: float
    after: float
    reason: str


@dataclass
class Genome:
    """Mutable trait set that drives organism behavior."""

    genes: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_GENES))
    generation: int = 0
    complexity: float = 1.0
    unlocked_modules: List[str] = field(default_factory=lambda: ["core"])
    mutation_log: List[GeneLogEntry] = field(default_factory=list)
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.seed is None:
            self.seed = random.randint(1, 2**31 - 1)
        # Clamp all genes into safe range.
        for k, v in list(self.genes.items()):
            self.genes[k] = self._clamp(float(v))

    @staticmethod
    def _clamp(value: float) -> float:
        return max(GENE_MIN, min(GENE_MAX, value))

    def get(self, name: str, default: float = 0.3) -> float:
        return float(self.genes.get(name, default))

    def set_gene(self, name: str, value: float, tick: int = 0, reason: str = "") -> None:
        before = self.genes.get(name, 0.0)
        after = self._clamp(value)
        self.genes[name] = after
        self.mutation_log.append(
            GeneLogEntry(tick=tick, gene=name, before=before, after=after, reason=reason)
        )
        # Keep log bounded.
        if len(self.mutation_log) > 200:
            self.mutation_log = self.mutation_log[-200:]

    def nudge(
        self,
        name: str,
        delta: float,
        tick: int = 0,
        reason: str = "nudge",
    ) -> float:
        """Apply a small change; stability dampens, sensitivity amplifies."""
        stability = self.get("stability")
        sensitivity = self.get("sensitivity")
        effective = delta * (0.5 + sensitivity) * (1.2 - stability * 0.8)
        new_val = self.get(name) + effective
        self.set_gene(name, new_val, tick=tick, reason=reason)
        return self.get(name)

    def fingerprint(self) -> str:
        payload = json.dumps(
            {"g": self.genes, "gen": self.generation, "c": round(self.complexity, 4)},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    def raise_complexity(self, amount: float = 0.05) -> None:
        self.complexity = min(100.0, self.complexity + max(0.0, amount))

    def unlock(self, module_name: str) -> bool:
        if module_name not in self.unlocked_modules:
            self.unlocked_modules.append(module_name)
            self.raise_complexity(0.35)
            return True
        return False

    def has_module(self, module_name: str) -> bool:
        return module_name in self.unlocked_modules

    def snapshot(self) -> Dict[str, Any]:
        return {
            "genes": dict(self.genes),
            "generation": self.generation,
            "complexity": self.complexity,
            "unlocked_modules": list(self.unlocked_modules),
            "seed": self.seed,
            "fingerprint": self.fingerprint(),
            "recent_mutations": [
                {
                    "tick": e.tick,
                    "gene": e.gene,
                    "before": round(e.before, 4),
                    "after": round(e.after, 4),
                    "reason": e.reason,
                }
                for e in self.mutation_log[-12:]
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genes": dict(self.genes),
            "generation": self.generation,
            "complexity": self.complexity,
            "unlocked_modules": list(self.unlocked_modules),
            "seed": self.seed,
            "mutation_log": [
                {
                    "tick": e.tick,
                    "gene": e.gene,
                    "before": e.before,
                    "after": e.after,
                    "reason": e.reason,
                }
                for e in self.mutation_log[-100:]
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Genome":
        log = [
            GeneLogEntry(**entry)
            for entry in data.get("mutation_log", [])
            if isinstance(entry, dict) and "gene" in entry
        ]
        return cls(
            genes=dict(data.get("genes", DEFAULT_GENES)),
            generation=int(data.get("generation", 0)),
            complexity=float(data.get("complexity", 1.0)),
            unlocked_modules=list(data.get("unlocked_modules", ["core"])),
            mutation_log=log,
            seed=data.get("seed"),
        )

    def clone(self) -> "Genome":
        return Genome.from_dict(deepcopy(self.to_dict()))
