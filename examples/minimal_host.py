#!/usr/bin/env python3
"""
Minimal host program — drop-in pattern for any existing Python app.

Run from the project root:

    python examples/minimal_host.py
"""

from __future__ import annotations

import os
import sys
import time

# Allow running without install: add project root to path.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from symbio_engine import SymbioEngine, symbio_hook


def main() -> None:
    # Fresh demo each run so newcomers always see the same story arc.
    # Pass --persist to grow Wally across sessions.
    persist = "--persist" in sys.argv
    state = os.path.join(ROOT, "examples", "minimal_state.json")
    engine = SymbioEngine(
        name="Wally",
        state_path=state,
        auto_load=persist,
        auto_save=persist,
        seed=42,
    )
    engine.boot(force_fresh=not persist)
    engine.attach_globals()

    @engine.hook("player_action", intensity=0.55)
    def do_work(n: int = 1) -> int:
        return n * 2

    @engine.hook("fragile", intensity=0.3, default=0)
    def fragile_divide(a: int, b: int) -> float:
        return a / b

    print("── Minimal host + SymbioEngine ──")
    if persist:
        print("(persistent mode — growing across runs)")
    print(engine.narrative())
    print()

    for i in range(12):
        result = do_work(i + 1)
        engine.push_metric("workload", float(i) / 12.0)
        # Deliberately trip the healer a few times (division by zero).
        if i % 3 == 0:
            healed = fragile_divide(10, 0)
            print(f"  tick={i:02d} work={result} fragile_healed={healed}")
        else:
            print(f"  tick={i:02d} work={result}")
        engine.observe("score", value=float(i), intensity=0.3)
        engine.pulse(0.05)
        time.sleep(0.02)

    print()
    print(engine.narrative())
    print()
    if persist:
        print("Saved to:", engine.save())
    else:
        print("Tip: run with --persist to save growth between sessions.")
    engine.shutdown()


if __name__ == "__main__":
    main()
