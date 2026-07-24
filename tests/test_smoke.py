#!/usr/bin/env python3
"""Regression / smoke suite for SymbioEngine (stdlib unittest)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from symbio_engine import SymbioEngine, __version__
from symbio_engine.events import EventBus
from symbio_engine.genome import Genome
from symbio_engine.organism import Organism
from symbio_engine.persistence import Persistence


class TestGenome(unittest.TestCase):
    def test_clamp(self) -> None:
        g = Genome()
        g.set_gene("curiosity", 5.0)
        self.assertLessEqual(g.get("curiosity"), 0.99)
        g.set_gene("curiosity", -1.0)
        self.assertGreaterEqual(g.get("curiosity"), 0.01)

    def test_fingerprint_stable(self) -> None:
        g = Genome(seed=1)
        a = g.fingerprint()
        b = g.fingerprint()
        self.assertEqual(a, b)


class TestEventBus(unittest.TestCase):
    def test_emit_and_history(self) -> None:
        bus = EventBus()
        seen = []
        bus.on("ping", lambda e: seen.append(e.name))
        bus.emit("ping", {"x": 1})
        self.assertEqual(seen, ["ping"])
        self.assertEqual(bus.recent_names(1), ["ping"])

    def test_handler_exception_isolated(self) -> None:
        bus = EventBus()

        def bad(_e):
            raise RuntimeError("handler boom")

        bus.on("x", bad)
        # Must not raise out of the bus.
        bus.emit("x")


class TestPersistence(unittest.TestCase):
    def test_roundtrip(self) -> None:
        td = tempfile.mkdtemp()
        path = os.path.join(td, "s.json")
        org = Organism(name="Wally")
        org.register_interaction("hi")
        org.meta["bond"] = 0.42
        pers = Persistence(path)
        pers.save(org)
        data = pers.load()
        assert data is not None
        org2 = Organism.from_dict(data["organism"])
        self.assertEqual(org2.name, "Wally")
        self.assertEqual(org2.interactions, 1)
        self.assertEqual(org2.meta.get("bond"), 0.42)


class TestEngine(unittest.TestCase):
    def _fresh(self, **kw) -> SymbioEngine:
        td = tempfile.mkdtemp()
        path = os.path.join(td, "e.json")
        defaults = dict(
            name="Wally",
            state_path=path,
            auto_load=False,
            auto_save=False,
            seed=99,
        )
        defaults.update(kw)
        eng = SymbioEngine(**defaults)
        eng.boot(force_fresh=True)
        return eng

    def test_version(self) -> None:
        self.assertTrue(__version__)

    def test_heal_zero_division(self) -> None:
        e = self._fresh()
        r = e.safe_call(lambda a, b: a / b, 1, 0, default=99, label="div")
        self.assertEqual(r, 99)
        self.assertGreaterEqual(e.organism.errors_healed, 1)

    def test_interact_and_pulse(self) -> None:
        e = self._fresh()
        e.interact("touch", intensity=0.5)
        info = e.pulse(0.05)
        self.assertTrue(info["alive"])
        self.assertGreaterEqual(info["tick"], 1)
        self.assertGreaterEqual(e.organism.interactions, 1)

    def test_dormant_pulse(self) -> None:
        e = self._fresh()
        e.organism.alive = False
        st = e.pulse()
        self.assertFalse(st.get("alive"))

    def test_emergence_restore_preserves_meta(self) -> None:
        td = tempfile.mkdtemp()
        path = os.path.join(td, "restore.json")
        e = SymbioEngine(
            name="Wally",
            state_path=path,
            auto_load=False,
            auto_save=True,
            seed=3,
        )
        e.boot(force_fresh=True)
        # Force unlock an emergent module and set living meta.
        e.organism.genome.complexity = 10.0
        e.organism.genome.generation = 5
        e.organism.interactions = 20
        for gene in e.organism.genome.genes:
            e.organism.genome.genes[gene] = 0.8
        newly = e.emergence.evaluate(e.organism)
        self.assertTrue(newly)
        # Stamp meta that must survive reload.
        e.organism.meta["symbiosis"] = 0.77
        e.organism.meta["tempo"] = 1.55
        e.save()
        e.shutdown()

        e2 = SymbioEngine(
            name="Wally",
            state_path=path,
            auto_load=True,
            auto_save=False,
            seed=3,
        )
        e2.boot()
        self.assertTrue(e2.emergence.active)
        self.assertEqual(e2.organism.meta.get("symbiosis"), 0.77)
        self.assertEqual(e2.organism.meta.get("tempo"), 1.55)
        # First pulse should not wipe restored meta via re-awaken.
        e2.pulse(0.05)
        self.assertEqual(e2.organism.meta.get("symbiosis"), 0.77)

    def test_runtime_patch_return_default(self) -> None:
        e = self._fresh()

        def boom():
            raise RuntimeError("always fails")

        # Chronic RuntimeErrors escalate to evolve; signature needs 2 evolve
        # sightings before a patch is invented (healer prefers default early).
        for _ in range(6):
            r = e.safe_call(boom, default=-7, label="boom")
            self.assertEqual(r, -7)
        patches = list(e.debugger.patches.values())
        self.assertTrue(patches)
        self.assertEqual(patches[0].strategy, "return_default")

    def test_evolve_callable_learns(self) -> None:
        e = self._fresh()

        def flaky(x: int) -> int:
            if x % 2 == 0:
                raise RuntimeError("even cursed")
            return x * 3

        evolved = e.evolve(flaky, default=-1, label="flaky")
        results = []
        for x in range(6):
            try:
                results.append(evolved(x))
            except Exception:
                results.append(e.safe_call(flaky, x, default=-1, label="flaky"))
        # Even inputs heal to default; odd inputs must still succeed.
        self.assertIn(-1, results)
        self.assertIn(3, results)   # flaky(1)
        self.assertIn(9, results)   # flaky(3)
        self.assertIn(15, results)  # flaky(5)

    def test_coerce_heal(self) -> None:
        e = self._fresh()

        def add_ints(a, b):
            if not isinstance(a, int) or not isinstance(b, int):
                raise TypeError("ints only")
            return a + b

        r = e.safe_call(add_ints, "2", "3", default=0, label="add_ints")
        self.assertEqual(r, 5)

    def test_status_path_is_relative_when_possible(self) -> None:
        e = self._fresh()
        st = e.status()
        path = st["engine"]["state_path"]
        # Should not embed a full Windows user home path when relpath works.
        self.assertNotIn("OneDrive", path)
        self.assertNotIn("Users\\", path.replace("/", "\\"))

    def test_narrative(self) -> None:
        e = self._fresh()
        text = e.narrative()
        self.assertIn("Wally", text)
        self.assertIn("Genes:", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
