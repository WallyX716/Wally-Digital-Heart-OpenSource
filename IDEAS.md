================================================================================
Wally Digital Heart · 5 Easy Ideas to Extend
Beginner-friendly, fun, and exciting
================================================================================

Each idea is small enough for a weekend (or a single enthusiastic evening).
They all plug into the existing SymbioEngine without rewriting the core.


--------------------------------------------------------------------------------
IDEA 1 — “Tamagotchi Terminal”
A tiny daily pet for your command line
--------------------------------------------------------------------------------

What to build:
  A script that loads Wally each morning, asks you one question
  (“Did you drink water?” / “Ship something today?”), maps the answer to
  interact/success/damage events, prints the narrative, and saves state.

How it connects:
  SymbioEngine(state_path="daily_wally.json", auto_load=True, auto_save=True)
  engine.interact(...) / engine.observe("success"|"damage", ...)
  engine.pulse(); print(engine.narrative())

Beginner steps:
  1. Copy examples/console_life.py as a starting point
  2. Replace free commands with 3 multiple-choice prompts
  3. Map answers to intensity + valence
  4. Show emergent modules as “mood stickers” in the text UI

Why it’s exciting:
  People bond with daily loops. Wally becomes *their* creature.

Stretch:
  Windows Task Scheduler / cron to auto-launch at 9:00.


--------------------------------------------------------------------------------
IDEA 2 — “Glitch Garden” micro-game (Pygame)
Click weeds, feed the heart, survive your own bugs
--------------------------------------------------------------------------------

What to build:
  A small Pygame scene: living orb (already in pygame_integration.py),
  falling “glitch bugs” that call safe_call on bad math, and flowers that
  bloom when complexity crosses thresholds.

How it connects:
  Reuse examples/pygame_integration.py
  engine.safe_call for bug collisions
  engine.on("emergence", ...) to spawn a flower particle burst
  engine.push_metric("fps", ...)

Beginner steps:
  1. Run the existing pygame demo until it feels familiar
  2. Add a list of bug rects that move down the screen
  3. On click-hit, engine.interact("squash"); on miss, raise a harmless error
  4. When emergence fires, draw a new flower sprite

Why it’s exciting:
  Players *see* self-healing and emergence — the UI becomes the organism.

Stretch:
  High-score that is actually organism generation + modules unlocked.


--------------------------------------------------------------------------------
IDEA 3 — “Study Buddy Stress Meter”
Help students notice load — without creepy surveillance
--------------------------------------------------------------------------------

What to build:
  A study timer that pulses Wally every minute. Long focus streaks send
  success events; frantic app-switching (manual button) sends threat/stress.
  Immune Reflex / Chronos Sense become study insights in plain language.

How it connects:
  engine.observe("success", intensity=...) on completed pomodoros
  engine.observe("threat", intensity=...) on “I’m overwhelmed” button
  Read engine.organism.stress and engine.emergence.active for tips

Beginner steps:
  1. Write a 25-minute countdown in pure Python
  2. Each minute: engine.pulse(60)
  3. End of session: print narrative + one tip based on stress/mood
  4. Optional: --persist so semester-long growth is real

Why it’s exciting:
  Useful *and* playful; great classroom demo for creative coding.

Privacy note:
  Only use buttons the user presses — don’t scrape personal files.


--------------------------------------------------------------------------------
IDEA 4 — “Module Workshop” — invent one new emergent behavior
--------------------------------------------------------------------------------

What to build:
  A single new module in EMERGENT_CATALOG, for example:

    name: "spark_journal"
    title: "Spark Journal"
    description: "After bright successes, writes a short victory note to memory."

How it connects:
  Edit symbio_engine/emergence.py (see README “Extending”)
  on_event: if event.name in ("success","score") and intensity high → remember()
  Unlock when creativity + complexity cross gentle thresholds

Beginner steps:
  1. Copy an existing EmergentModule block as a template
  2. Lower min_complexity so you can unlock it in minimal_host quickly
  3. Run demos until you see the EMERGENCE printout
  4. Open a PR / share a screenshot of the narrative line

Why it’s exciting:
  One file change → new personality. Perfect first contribution.

Stretch:
  Host reverse-hook: ask_host("play_sound", "spark.wav") on awaken.


--------------------------------------------------------------------------------
IDEA 5 — “Twin Engines” experiment — cooperation vs rivalry
--------------------------------------------------------------------------------

What to build:
  Two SymbioEngine instances (Wally & Ada) in one script. Each pulse, they
  sometimes mirror each other’s mood (empathy event) or compete for a shared
  score resource. Print a side-by-side story every 10 ticks.

How it connects:
  engine_a.observe(..., host_mood=engine_b.organism.mood)
  engine_b.interact("rivalry", intensity=...)
  Compare butterfly_index and complexity after N pulses

Beginner steps:
  1. Start from examples/minimal_host.py
  2. Construct two engines with different seeds and state paths
  3. Loop 50 times: random event to A or B; both pulse
  4. Print both narratives at the end

Why it’s exciting:
  Instant science-fair energy — emergent social dynamics from tiny rules.

Stretch:
  Graph complexity over time with a CSV + spreadsheet chart.


--------------------------------------------------------------------------------
PICKING YOUR FIRST IDEA
--------------------------------------------------------------------------------

Want something cozy?          → Idea 1 (Tamagotchi Terminal)
Want something visual?        → Idea 2 (Glitch Garden)
Want something useful?        → Idea 3 (Study Buddy)
Want a first open-source PR?  → Idea 4 (Module Workshop)
Want a weird experiment?      → Idea 5 (Twin Engines)

Whatever you build, keep the core stdlib-pure when you can, avoid committing
state JSON, and credit the heart of the project to Jonathan.


================================================================================
Happy growing.
================================================================================
