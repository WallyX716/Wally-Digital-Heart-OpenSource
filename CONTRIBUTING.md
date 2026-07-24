# Contributing to Wally Digital Heart (SymbioEngine)

Thanks for helping Wally grow. This project is maintained by **Jonathan** and welcomes beginners.

## Ways to contribute

- Fix bugs or improve docs/examples
- Add a gene cascade, heal strategy, or emergent module
- Share a host integration (CLI tool, bot, game loop)
- Report issues with clear reproduction steps

## Dev setup

```text
git clone <your-fork-url>
cd Wally-Digital-Heart-OpenSource
python -m venv .venv
```

Activate the venv (Windows PowerShell: `.\.venv\Scripts\Activate.ps1`, macOS/Linux: `source .venv/bin/activate`), then:

```text
pip install -e ".[dev]"
python examples/minimal_host.py
python examples/self_heal_lab.py
python examples/pygame_integration.py --headless
```

## Guidelines

1. **Keep the core stdlib-only.** Optional deps belong behind extras (e.g. `game`).
2. **No arbitrary `exec` of generated code.** Evolutionary patches stay strategy-based.
3. **Do not commit state JSON** (`*_state.json`) or secrets.
4. Prefer small, focused PRs with a short description of *why*.
5. Match existing style: type hints, short modules, clear docstrings.

## Suggesting a new emergent module

See `symbio_engine/emergence.py` and the README “Extending” section. Include:

- unlock thresholds (complexity / genes / prereqs)
- what `on_awaken` / `on_tick` / `on_event` do
- a tiny example or test idea

## Code of conduct (short)

Be kind. Assume good intent. No harassment. This is a creative, playful project — keep discussions constructive.
