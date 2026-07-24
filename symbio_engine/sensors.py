"""
Runtime sensors — harvest host metrics so the organism can feel the program.

Works without external deps. Hosts may push custom metrics via ``push()``.
"""

from __future__ import annotations

import os
import sys
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional


@dataclass
class Sample:
    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class SensorSuite:
    """Collects lightweight runtime signals for mutation pressure."""

    def __init__(self, history: int = 120) -> None:
        self._history: Deque[Sample] = deque(maxlen=history)
        self._custom: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._last_snapshot: Dict[str, Any] = {}
        self._t0 = time.time()
        self._last_cpu_time = time.process_time()
        self._last_wall = self._t0

    def push(
        self,
        name: str,
        value: float,
        unit: str = "",
        **tags: str,
    ) -> Sample:
        sample = Sample(name=name, value=float(value), unit=unit, tags=dict(tags))
        with self._lock:
            self._history.append(sample)
            self._custom[name] = sample.value
        return sample

    def read_system(self) -> Dict[str, float]:
        """Best-effort process metrics (stdlib only)."""
        now = time.time()
        cpu_now = time.process_time()
        wall_delta = max(1e-6, now - self._last_wall)
        cpu_delta = cpu_now - self._last_cpu_time
        cpu_ratio = max(0.0, min(4.0, cpu_delta / wall_delta))
        self._last_cpu_time = cpu_now
        self._last_wall = now

        metrics = {
            "uptime_s": now - self._t0,
            "cpu_ratio": cpu_ratio,
            "thread_count": float(threading.active_count()),
            "python_version": float(sys.version_info.major)
            + sys.version_info.minor / 10.0,
        }
        # Optional: memory via resource (Unix) or skip on Windows.
        try:
            import resource  # type: ignore

            usage = resource.getrusage(resource.RUSAGE_SELF)
            metrics["max_rss_mb"] = float(usage.ru_maxrss) / 1024.0
        except Exception:
            metrics["max_rss_mb"] = -1.0

        metrics["pid"] = float(os.getpid())
        with self._lock:
            for k, v in metrics.items():
                self._history.append(Sample(name=k, value=v, unit="auto"))
            self._last_snapshot = dict(metrics)
            self._last_snapshot.update(self._custom)
        return dict(self._last_snapshot)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            custom = dict(self._custom)
            recent = [
                {
                    "name": s.name,
                    "value": s.value,
                    "unit": s.unit,
                    "t": s.timestamp,
                }
                for s in list(self._history)[-20:]
            ]
        sys_m = self.read_system()
        return {"system": sys_m, "custom": custom, "recent": recent}

    def as_mutation_events(self) -> List[Dict[str, Any]]:
        """
        Convert notable metrics into event-like dicts the engine can ingest.
        """
        snap = self.read_system()
        events: List[Dict[str, Any]] = []
        cpu = snap.get("cpu_ratio", 0.0)
        events.append(
            {
                "name": "runtime_metric",
                "payload": {
                    "metric": "cpu_ratio",
                    "value": cpu,
                    "baseline": 0.5,
                    "higher_is_better": False,
                    "intensity": min(1.0, abs(cpu - 0.5)),
                },
            }
        )
        threads = snap.get("thread_count", 1.0)
        events.append(
            {
                "name": "runtime_metric",
                "payload": {
                    "metric": "thread_count",
                    "value": threads,
                    "baseline": 4.0,
                    "higher_is_better": False,
                    "intensity": 0.2,
                },
            }
        )
        for name, value in list(self._custom.items())[:8]:
            events.append(
                {
                    "name": "runtime_metric",
                    "payload": {
                        "metric": name,
                        "value": value,
                        "baseline": 0.5,
                        "higher_is_better": True,
                        "intensity": 0.25,
                    },
                }
            )
        return events
