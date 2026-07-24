# Wally Digital Heart · SymbioEngine

**A lightweight living digital organism for any Python program or Pygame game.**

Created by **Jonathan**.

SymbioEngine wraps a small modular core into something that *starts minimal*, then **grows complexity** from user interactions and runtime data. Small inputs cascade through a genome (butterfly-effect mutations). Errors are **self-healed**. Repeated failures invent **evolutionary code patches**. Over time, **2041-style emergent modules** awaken: dream weaver, pattern prophet, true symbiote, inner polyphony, and more.

- **Pure Python 3.9+** core (stdlib only — no hard dependencies)
- **Importable** into existing apps with a few lines
- **Hooks** for host → organism and organism → host
- **Runnable demos** included (console, minimal host, pygame/headless)
- **Persistent** state across sessions (optional JSON checkpoint)

---

## Quick start

From the project root:

```text
python examples/minimal_host.py
python examples/self_heal_lab.py
python examples/pygame_integration.py --headless
python examples/console_life.py
```

Optional visual demo:

```text
pip install pygame
python examples/pygame_integration.py
```

Grow across sessions:

```text
python examples/minimal_host.py --persist
python examples/pygame_integration.py --headless --persist
```

---

## Install / import into your project

### Option A — path import (zero install)

```python
import sys
from pathlib import Path

# Point this at the folder that contains the `symbio_engine` package.
sys.path.insert(0, str(Path(__file__).resolve().parent / "Wally-Digital-Heart-OpenSource"))

from symbio_engine import SymbioEngine

engine = SymbioEngine(name="Wally")
engine.boot()
```

### Option B — editable install

```text
cd Wally-Digital-Heart-OpenSource
pip install -e .
```

Optional Pygame extra:

```text
pip install -e ".[game]"
```

Then:

```python
from symbio_engine import SymbioEngine
```

---

## 60-second integration

```python
from symbio_engine import SymbioEngine

engine = SymbioEngine(name="Wally", state_path="wally_state.json")
engine.boot()
engine.attach_globals()  # enables @symbio_hook without passing engine

# 1) Decorate host functions — feeds the organism + self-heals
@engine.hook("player_action", intensity=0.5, default=None)
def jump():
    # your game logic
    ...

# 2) Observe runtime signals (FPS, score, damage, …)
engine.push_metric("fps", 0.92)
engine.observe("score", value=1200, intensity=0.4)
engine.interact("menu_open", intensity=0.3)

# 3) Once per frame / tick
info = engine.pulse(dt)
# info → health, mood, complexity, generation, emergent modules, butterfly index

# 4) Safe calls for risky code
result = engine.safe_call(risky_fn, *args, default=0, label="risky_fn")

# 5) Listen for emergence
engine.on("emergence", lambda e: print("Awakened:", e.payload["title"]))

# 6) Shutdown (autosaves when auto_save=True)
engine.shutdown()
```

### Pygame sketch

```python
import pygame
from symbio_engine import SymbioEngine

engine = SymbioEngine(name="Wally").boot()
pygame.init()
screen = pygame.display.set_mode((640, 360))
clock = pygame.time.Clock()

@engine.hook("player_action", intensity=0.45)
def on_click(pos):
    ...

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            on_click(event.pos)
            engine.observe("click", intensity=0.5, valence=0.2)

    engine.push_metric("fps", clock.get_fps() / 60.0)
    status = engine.pulse(dt)
    # tint UI from status["mood"], status["health"], status["emergent"]
    ...
engine.shutdown()
```

See `examples/pygame_integration.py` for a complete windowed + headless version.

---

## How it works

```text
┌─────────────────────────────────────────────────────────────┐
│                     Your program / game                      │
│   hooks · observe() · push_metric() · safe_call() · pulse() │
└───────────────────────────┬─────────────────────────────────┘
                            │ events / callables
┌───────────────────────────▼─────────────────────────────────┐
│                      SymbioEngine                            │
│  EventBus ──► MutationEngine ──► Genome (genes + complexity) │
│       │              │                                       │
│       ▼              ▼                                       │
│  EmergenceController   Organism (vitality, mood, memory)     │
│       │                                                      │
│  SelfHealer ◄──► EvolutionaryDebugger (safe strategy patches)│
│       │                                                      │
│  SensorSuite · Persistence (JSON checkpoint)                 │
└─────────────────────────────────────────────────────────────┘
```

### 1. Starts minimal

A newborn organism has:

| Piece | Starting point |
|--------|----------------|
| Genes | Small set: resilience, curiosity, sensitivity, adaptability, memory_depth, empathy, creativity, stability |
| Complexity | `1.0` |
| Modules | `["core"]` only |
| Emergent behaviors | None (latent) |

Nothing fancy is pre-scripted as “always on.” Rich behavior is **earned**.

### 2. Butterfly-effect mutations

Every host event (`interaction`, `click`, `score`, `error`, metrics, …) applies **pressures** to one or more genes. Those primary nudges **cascade** through a graph:

```text
curiosity  → creativity, sensitivity
sensitivity → empathy, stress
creativity  → curiosity, (slight) −stability
…
```

Amplification depends on **sensitivity** and is damped by **stability**. A single click can therefore ripple into mood, later unlock creativity thresholds, raise complexity, and eventually awaken a new module.

Inspect live sensitivity:

```python
engine.mutator.butterfly_index(engine.organism)  # 0..1
```

### 3. Self-healing errors

`engine.safe_call(fn, …)` and `@engine.hook(..., heal=True)` wrap callables with `SelfHealer`:

| Strategy | Role |
|----------|------|
| `retry` | Short backoff re-invoke |
| `default` | Return a safe default |
| `skip` | Swallow and continue |
| `coerce` | Best-effort type coercion, then retry |
| `evolve` | Hand off to the evolutionary debugger |

Chronic error classes escalate toward `evolve`. Successful heals lower stress, raise resilience, and write memory episodes.

### 4. Self-debug via evolutionary patches

`EvolutionaryDebugger` does **not** `exec` arbitrary source (safe for games). It invents **strategy patches** for failure signatures:

- `return_default`
- `clamp_numeric_args`
- `ignore_extra_kwargs`
- `retry_once`
- `swap_arg_order`
- `log_and_neutralize`

After the same signature fails twice, a patch is born, stored on the organism, and reapplied on future calls. Patches persist across sessions with the organism state.

```python
stable_fn = engine.evolve(flaky_fn, default=-1, label="flaky")
stable_fn(0)  # learns over repeated failures
```

### 5. Organic feature growth (emergence)

`EmergenceController` watches complexity, generation, interactions, gene floors, and prerequisites. When thresholds pass, modules **awaken**:

| Module | Vibe (2041 palette) |
|--------|---------------------|
| **Echo Chamber** | Mirrors host emotional valence |
| **Dream Weaver** | Idle gaps recombine memories into dreams |
| **Pattern Prophet** | Forecasts likely next host events |
| **Immune Reflex** | Autonomic stress purge |
| **True Symbiote** | Deep host co-regulation / bond meter |
| **Inner Polyphony** | Multiple internal voices debate state |
| **Chronos Sense** | Subjective tempo warps with curiosity & stress |

Listen:

```python
engine.on("emergence", lambda e: print(e.payload["title"], e.payload["description"]))
```

After a save/load, previously unlocked modules are **restored** without resetting their living meta (bond meters, tempos, dreams).

### 6. Sensors & runtime data

```python
engine.push_metric("fps", 0.9)
engine.push_metric("latency_ms", 42)
engine.sensors.read_system()  # cpu_ratio, threads, uptime, …
```

Metrics become mutation pressure so the organism *feels* how the host program is performing.

### 7. Persistence

By default the engine can checkpoint organism + debugger patches to JSON:

```python
engine = SymbioEngine(state_path="wally_state.json", auto_load=True, auto_save=True)
engine.save()       # manual
engine.shutdown()   # final save
```

Reload on next boot continues generation, genes, memory, patches, and emergent modules — growth across sessions.

---

## Package map

```text
Wally-Digital-Heart-OpenSource/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── symbio_engine/
│   ├── __init__.py      # public exports
│   ├── engine.py        # SymbioEngine façade
│   ├── organism.py      # vitality, mood, memory
│   ├── genome.py        # genes, complexity, modules
│   ├── mutation.py      # butterfly cascades
│   ├── healer.py        # self-heal strategies
│   ├── debugger.py      # evolutionary patches
│   ├── emergence.py     # 2041 module catalog
│   ├── sensors.py       # runtime metrics
│   ├── events.py        # EventBus
│   ├── hooks.py         # decorators & host callbacks
│   └── persistence.py   # JSON save/load
└── examples/
    ├── minimal_host.py
    ├── console_life.py
    ├── pygame_integration.py
    └── self_heal_lab.py
```

---

## API reference (essentials)

### `SymbioEngine(name, seed=None, state_path=None, auto_save=True, auto_load=True)`

| Method | Purpose |
|--------|---------|
| `boot(force_fresh=False)` | Init / restore / bind listeners |
| `attach_globals()` | Default engine for module-level decorators |
| `pulse(dt=None)` | Heartbeat — call every frame |
| `emit(name, payload=None, source="host")` | Raw event |
| `observe(name, **payload)` | Host signal shorthand |
| `interact(label, intensity=0.4)` | Friendly interaction event |
| `push_metric(name, value, unit="")` | Custom sensor sample |
| `safe_call(fn, *args, default=None, label="")` | Healed invocation |
| `evolve(fn, default=None, label="")` | Return self-patching callable |
| `hook(event_name, intensity=0.4, heal=True, default=None)` | Decorator factory |
| `on(event_name, handler)` | Subscribe to bus |
| `register_host(name, fn)` / `ask_host(name, …)` | Reverse hooks |
| `status()` | Full structured snapshot |
| `narrative()` | Human-readable portrait |
| `save()` / `shutdown()` | Persist / teardown |

### Decorators (`symbio_engine.hooks`)

```python
from symbio_engine import symbio_hook, on_event, host_callback

@symbio_hook("player_action", intensity=0.5)  # needs attach_globals()
def action(): ...

@on_event("emergence")
def celebrate(event): ...

@host_callback("flash_screen")
def flash(color=(255, 0, 0)): ...
```

### Useful event names

| Event | Typical source | Effect |
|-------|----------------|--------|
| `interaction` / `click` / `player_action` | host | curiosity↑ sensitivity↑ |
| `success` / `score` / `reward` | host | mood↑ creativity↑ |
| `error` / `exception` | host/healer | resilience↑ adaptability↑ |
| `damage` / `threat` | host | stress↑ resilience↑ |
| `runtime_metric` / `fps` | sensors/host | adaptability pressure |
| `tick` / `pulse` | organism | ambient drift |
| `emergence` | organism | module awakened |
| `boot` / `shutdown` | organism | lifecycle |

---

## Design principles

1. **Real and runnable** — no mock-only stubs; demos execute on a stock CPython.
2. **Safe evolution** — patches are strategy tokens, not remote code execution.
3. **Modular** — swap or extend `EMERGENT_CATALOG`, cascade graph, heal strategies.
4. **Host-agnostic** — works in CLI scripts, services, and game loops.
5. **Lightweight** — pulse work is O(active modules + small history); sensors throttled.
6. **Living continuity** — JSON memory so Wally can grow between runs.

---

## Extending

### Add a gene cascade

Edit `CASCADE_GRAPH` in `symbio_engine/mutation.py`.

### Add an emergent module

```python
from symbio_engine.emergence import EmergentModule, EMERGENT_CATALOG

EMERGENT_CATALOG.append(
    EmergentModule(
        name="night_vision",
        title="Night Vision",
        description="Heightened sensitivity after many dark idle pulses.",
        min_complexity=4.5,
        min_gene={"sensitivity": 0.5},
        on_tick=lambda org, dt: org.meta.update(night=org.stress < 0.2),
    )
)
```

### Custom heal strategy table

```python
engine.healer.STRATEGY_TABLE["MyError"] = ["retry", "default", "evolve"]
```

---

## Examples in detail

| Script | What it shows |
|--------|----------------|
| `examples/minimal_host.py` | Drop-in pattern + heal on divide-by-zero (`--persist` optional) |
| `examples/self_heal_lab.py` | Chronic faults → evolutionary patches |
| `examples/console_life.py` | Interactive life: touch, error, pulse, story, reset |
| `examples/pygame_integration.py` | Full game loop; auto headless if no pygame |

---

## Requirements

- **Python 3.9+**
- Core: **no third-party packages**
- Optional: `pygame>=2.5` for the windowed demo

---

## License

MIT © Jonathan — use it in games, tools, experiments, or as the heart of something stranger.

---

*Wally Digital Heart · SymbioEngine 0.1.1 · grow carefully · by Jonathan*
