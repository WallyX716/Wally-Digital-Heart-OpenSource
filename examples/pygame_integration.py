#!/usr/bin/env python3
"""
Pygame-style integration example.

Works in two modes:
  1. With pygame installed — full interactive window.
  2. Without pygame — headless simulation of the same game loop so the
     prototype stays runnable anywhere.

Run:

    python examples/pygame_integration.py
    python examples/pygame_integration.py --headless
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from symbio_engine import SymbioEngine


def try_import_pygame():
    try:
        import pygame  # type: ignore

        return pygame
    except ImportError:
        return None


def headless_loop(engine: SymbioEngine, seconds: float = 6.0) -> None:
    """Simulate a game loop without a display."""
    print("── Headless Pygame-style loop ──")
    t0 = time.time()
    frame = 0
    actions = ["move", "jump", "collect", "idle", "hit"]
    while time.time() - t0 < seconds:
        frame += 1
        action = actions[frame % len(actions)]
        if action != "idle":
            engine.interact(action, intensity=0.35 + 0.1 * (frame % 3))
        if action == "hit":
            # Simulate a risky gameplay function that sometimes fails.
            def risky_score(combo: int) -> int:
                if combo % 7 == 0:
                    raise ValueError("combo overflow")
                return combo * 10

            score = engine.safe_call(risky_score, frame, default=0, label="score")
            engine.observe("score", value=float(score), intensity=0.4)
        # Fake FPS metric.
        fps = 60.0 - 10.0 * math.sin(frame / 15.0)
        engine.push_metric("fps", fps / 60.0)
        info = engine.pulse(1.0 / 60.0)
        if frame % 30 == 0:
            print(
                f"  f={frame:04d} action={action:7s} "
                f"hp={info['health']:.2f} mood={info['mood']:.2f} "
                f"cx={info['complexity']:.2f} gen={info['generation']} "
                f"em={info['emergent']}"
            )
        time.sleep(0.01)
    print()
    print(engine.narrative())


def pygame_loop(engine: SymbioEngine, pygame) -> None:
    pygame.init()
    w, h = 720, 420
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("SymbioEngine × Pygame — Wally Digital Heart")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    big = pygame.font.SysFont("consolas", 22, bold=True)

    # Organism visualized as a living orb.
    cx, cy = w // 2, h // 2
    running = True
    particles = []

    @engine.hook("player_action", intensity=0.5)
    def on_click(pos):
        particles.append({"pos": list(pos), "life": 30})
        return pos

    engine.register_host(
        "on_emergence",
        lambda name, title: particles.append(
            {"pos": [cx, cy], "life": 90, "flash": True}
        ),
    )

    while running:
        dt_ms = clock.tick(60)
        dt = dt_ms / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    engine.interact("space", intensity=0.6)
                elif event.key == pygame.K_e:
                    def bad():
                        raise RuntimeError("player glitch")

                    engine.safe_call(bad, default=None, label="glitch")
                elif event.key == pygame.K_s:
                    engine.observe("success", intensity=0.8)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                on_click(event.pos)
                engine.observe(
                    "click",
                    intensity=0.5,
                    x=event.pos[0],
                    y=event.pos[1],
                    valence=0.3,
                )

        engine.push_metric("fps", clock.get_fps() / 60.0 if clock.get_fps() else 0.5)
        info = engine.pulse(dt)
        org = engine.organism

        # Background tinted by mood / stress.
        mood = org.mood
        stress = org.stress
        bg = (
            int(20 + stress * 40),
            int(18 + mood * 50),
            int(28 + (1 - stress) * 40),
        )
        screen.fill(bg)

        # Living orb: radius from vitality, color from genes.
        radius = int(40 + org.vitality * 50 + math.sin(org.age_ticks / 8.0) * 6)
        color = (
            int(80 + org.genome.get("curiosity") * 150),
            int(80 + org.genome.get("empathy") * 150),
            int(100 + org.genome.get("creativity") * 140),
        )
        pygame.draw.circle(screen, color, (cx, cy), radius)
        rim = int(200 * org.health)
        pygame.draw.circle(screen, (rim, rim, 255), (cx, cy), radius, 3)

        # Particles
        for p in particles[:]:
            p["life"] -= 1
            if p["life"] <= 0:
                particles.remove(p)
                continue
            r = max(2, p["life"] // 3)
            col = (255, 220, 120) if p.get("flash") else (180, 220, 255)
            pygame.draw.circle(screen, col, (int(p["pos"][0]), int(p["pos"][1])), r)

        lines = [
            f"{org.name}  gen={info['generation']}  cx={info['complexity']:.2f}",
            f"health={info['health']:.2f} mood={info['mood']:.2f} butterfly={info['butterfly']:.2f}",
            f"emergent: {', '.join(info['emergent']) or '—'}",
            "click=interact  space=touch  e=error  s=success  esc=quit",
        ]
        screen.blit(big.render(lines[0], True, (240, 240, 255)), (16, 12))
        for i, line in enumerate(lines[1:]):
            screen.blit(font.render(line, True, (200, 210, 230)), (16, 44 + i * 20))

        # Gene bars
        y = h - 20 * len(org.genome.genes) - 12
        for gene, val in sorted(org.genome.genes.items()):
            screen.blit(font.render(gene[:12], True, (170, 180, 200)), (16, y))
            pygame.draw.rect(screen, (50, 50, 70), (110, y + 4, 120, 10))
            pygame.draw.rect(
                screen,
                (100, 200, 180),
                (110, y + 4, int(120 * val), 10),
            )
            y += 20

        pygame.display.flip()

    engine.shutdown()
    pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="SymbioEngine Pygame integration")
    parser.add_argument("--headless", action="store_true", help="No window")
    parser.add_argument("--seconds", type=float, default=6.0, help="Headless duration")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Load/save organism state across runs",
    )
    parser.add_argument("--seed", type=int, default=11, help="RNG seed for demos")
    args = parser.parse_args()

    state = os.path.join(ROOT, "examples", "pygame_state.json")
    engine = SymbioEngine(
        name="Wally",
        state_path=state,
        auto_load=args.persist,
        auto_save=args.persist,
        seed=args.seed,
    )
    engine.boot(force_fresh=not args.persist)
    engine.attach_globals()

    engine.on(
        "emergence",
        lambda ev: print(f"[emergence] {ev.payload.get('title')}"),
    )

    pg = None if args.headless else try_import_pygame()
    if pg is None:
        if not args.headless:
            print("pygame not installed — running headless simulation.")
            print("Install with: pip install pygame")
        headless_loop(engine, seconds=args.seconds)
        engine.shutdown()
    else:
        pygame_loop(engine, pg)


if __name__ == "__main__":
    main()
