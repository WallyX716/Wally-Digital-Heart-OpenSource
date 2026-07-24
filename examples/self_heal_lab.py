#!/usr/bin/env python3
"""
Lab demo: self-heal + evolutionary patches under repeated failures.

Run:

    python examples/self_heal_lab.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from symbio_engine import SymbioEngine


def main() -> None:
    engine = SymbioEngine(
        name="Wally-Lab",
        state_path=os.path.join(ROOT, "examples", "lab_state.json"),
        auto_load=False,
        auto_save=False,
        seed=7,
    )
    engine.boot(force_fresh=True)

    print("=== Self-heal & evolutionary patch lab ===\n")

    # 1) Simple heal: division by zero → default
    def divide(a, b):
        return a / b

    for _ in range(3):
        r = engine.safe_call(divide, 10, 0, default=float("nan"), label="divide")
        print(f"divide(10,0) healed -> {r}")

    # 2) Evolutionary path: chronic RuntimeError invents a return_default patch
    def flaky(x: int) -> int:
        if x % 2 == 0:
            raise RuntimeError("even numbers are cursed")
        return x * 3

    evolved = engine.evolve(flaky, default=-1, label="flaky")
    print("\nEvolved callable under stress:")
    for x in range(8):
        try:
            print(f"  flaky({x}) -> {evolved(x)}")
        except Exception as exc:
            # First sightings raise; after the chronic threshold a patch lands.
            r = engine.safe_call(flaky, x, default=-1, label="flaky")
            print(f"  flaky({x}) raised {type(exc).__name__}; safe -> {r}")
        engine.pulse(0.02)

    # 3) TypeError coerce strategy
    def add_ints(a, b):
        if not isinstance(a, int) or not isinstance(b, int):
            raise TypeError("ints only")
        return a + b

    r = engine.safe_call(add_ints, "2", "3", default=0, label="add_ints")
    print(f"\nadd_ints('2','3') coerce/heal -> {r}")

    patches = engine.debugger.stats().get("patches", [])
    if patches:
        print(f"\nInvented patch: {patches[0].get('id')} [{patches[0].get('strategy')}]")

    print("\n" + engine.narrative())
    print("\nHealer stats:", engine.healer.stats())
    print("Debugger stats:", engine.debugger.stats())
    engine.shutdown()


if __name__ == "__main__":
    main()
