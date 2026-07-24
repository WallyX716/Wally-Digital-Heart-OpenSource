#!/usr/bin/env python3
"""
Interactive console life-demo — watch butterfly mutations and emergence.

Run:

    python examples/console_life.py
"""

from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from symbio_engine import SymbioEngine


HELP = """
Commands:
  t / touch [label]   Host interaction (butterfly seed)
  e / error           Simulate a host error (self-heal + mutate)
  s / success         Reward signal
  m / metric <n>      Push a runtime metric 0..1
  p / pulse [n]       Advance n heartbeats (default 5)
  d / debug           Force evolutionary jolt
  status              Full status dump
  story               Narrative portrait
  save                Checkpoint to disk
  reset               Fresh organism (wipes saved state)
  quit                Exit
  help                This text
"""


def simulate_error(engine: SymbioEngine) -> None:
    def boom(x: int) -> int:
        if x < 3:
            raise RuntimeError(f"simulated fault #{x}")
        return x

    wrapped = engine.evolve(boom, default=-1, label="boom")
    for i in range(4):
        try:
            r = wrapped(i)
            print(f"  boom({i}) -> {r}")
        except Exception as exc:
            print(f"  boom({i}) raised {exc}")
            # Feed through safe_call path too.
            r = engine.safe_call(boom, i, default=-1, label="boom")
            print(f"  safe_call boom({i}) -> {r}")


def main() -> None:
    state = os.path.join(ROOT, "examples", "console_state.json")
    engine = SymbioEngine(name="Wally", state_path=state)
    engine.boot()

    engine.on(
        "emergence",
        lambda ev: print(
            f"\n  ✦ EMERGENCE: {ev.payload.get('title')} — {ev.payload.get('description')}\n"
        ),
    )

    print("SymbioEngine console life-demo  ·  Wally Digital Heart")
    print("Type 'help' for commands. Wally grows as you interact.")
    print(HELP)
    print(engine.narrative())

    while True:
        try:
            raw = input("\nwally> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd in ("q", "quit", "exit"):
            break
        if cmd in ("h", "help", "?"):
            print(HELP)
        elif cmd in ("t", "touch"):
            label = parts[1] if len(parts) > 1 else "hand"
            engine.interact(label, intensity=0.6)
            info = engine.pulse(0.1)
            print("  interaction recorded.")
            print(
                f"  butterfly={info['butterfly']:.2f}  "
                f"mood={info['mood']:.2f}  cx={info['complexity']:.2f}"
            )
        elif cmd in ("e", "error"):
            simulate_error(engine)
            engine.pulse(0.1)
        elif cmd in ("s", "success"):
            engine.observe("success", intensity=0.7, value=1.0)
            engine.pulse(0.1)
            print("  reward absorbed.")
        elif cmd in ("m", "metric"):
            try:
                val = float(parts[1]) if len(parts) > 1 else 0.5
            except ValueError:
                print("  usage: metric <number 0..1>")
                continue
            engine.push_metric("host_fps_norm", val)
            engine.observe(
                "fps",
                value=val,
                baseline=0.6,
                higher_is_better=True,
                intensity=0.4,
            )
            engine.pulse(0.1)
            print(f"  metric={val}")
        elif cmd in ("p", "pulse"):
            try:
                n = int(parts[1]) if len(parts) > 1 else 5
            except ValueError:
                print("  usage: pulse [n]")
                continue
            n = max(1, min(n, 500))
            info = {"tick": 0, "health": 0, "complexity": 0, "generation": 0}
            for _ in range(n):
                info = engine.pulse(0.05)
            print(
                f"  pulsed x{n}  tick={info['tick']} health={info['health']} "
                f"complexity={info['complexity']} gen={info['generation']}"
            )
            if info.get("emergent"):
                print(f"  emergent: {info['emergent']}")
        elif cmd in ("d", "debug"):
            report = engine.mutator.forced_evolution(engine.organism, strength=0.1)
            print("  forced evolution:", report.as_dict())
            engine.pulse(0.1)
        elif cmd == "status":
            import json

            blob = json.dumps(engine.status(), indent=2, default=str)
            print(blob if len(blob) <= 5000 else blob[:5000] + "\n  … (truncated)")
        elif cmd in ("story", "narrative"):
            print(engine.narrative())
        elif cmd == "save":
            saved = engine.save()
            # Show relative path when possible (portable, no host PII).
            try:
                saved = os.path.relpath(saved)
            except ValueError:
                pass
            print("  saved:", saved)
        elif cmd == "reset":
            engine.persistence.clear()
            engine.shutdown()
            engine = SymbioEngine(name="Wally", state_path=state, auto_load=False)
            engine.boot(force_fresh=True)
            engine.on(
                "emergence",
                lambda ev: print(
                    f"\n  ✦ EMERGENCE: {ev.payload.get('title')} — "
                    f"{ev.payload.get('description')}\n"
                ),
            )
            print("  fresh organism ready.")
            print(engine.narrative())
        else:
            # Free-form interaction text becomes a labeled touch.
            engine.interact(raw[:40], intensity=0.45)
            engine.pulse(0.1)
            print("  (treated as interaction)")

    engine.shutdown()
    print("Goodnight,", engine.organism.name)


if __name__ == "__main__":
    main()
