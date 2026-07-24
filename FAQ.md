================================================================================
Wally Digital Heart · FAQ & Q&A
For new users and first-time contributors
================================================================================

--------------------------------------------------------------------------------
GETTING STARTED
--------------------------------------------------------------------------------

Q: What is this project in one sentence?
A: A lightweight Python engine that embeds a living digital organism (Wally)
   into your programs and games — it mutates, self-heals, and grows emergent
   behaviors from real runtime interaction.

Q: What do I need installed?
A: Python 3.9 or newer. That’s enough for the core and most demos.
   Optional: pygame 2.5+ for the windowed visual demo.

Q: How do I run it without “installing” anything?
A: Open a terminal in the project root and run:
     python examples/minimal_host.py
   The examples automatically add the project root to sys.path.

Q: How do I install it as a package?
A: From the project root:
     pip install -e .
   Optional game extra:
     pip install -e ".[game]"

Q: It says “python is not recognized.” What now?
A: Install Python from https://www.python.org/downloads/ and enable
   “Add python to PATH”. On Windows you can also try:
     py examples/minimal_host.py


--------------------------------------------------------------------------------
CORE CONCEPTS
--------------------------------------------------------------------------------

Q: What is SymbioEngine vs Wally Digital Heart?
A: “Wally Digital Heart” is the project / product name. SymbioEngine is the
   Python package (`symbio_engine`) you import. Wally is the default organism
   name inside the engine.

Q: Does Wally use AI / LLMs / an API key?
A: No. Behavior comes from genes, mutations, heuristics, and unlock rules.
   Fully offline.

Q: Is growth random?
A: Partially. A seed controls the RNG. Same seed + same event sequence tends
   to behave similarly, but timing (dt) and ambient tick mutations add life.

Q: What is the “butterfly index”?
A: A 0..1 score of how chaotically sensitive the organism currently is —
   high sensitivity and curiosity with lower stability → bigger cascades.

Q: What are emergent modules?
A: Optional behaviors that *awaken* when complexity, generation, interactions,
   and gene thresholds are met (Echo Chamber, Dream Weaver, etc.). They are
   not all on at birth.

Q: Are evolutionary patches dangerous?
A: They are intentionally safe strategy tokens (return default, clamp numbers,
   retry, ignore extra kwargs, …). The engine does not `exec` generated source.


--------------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------------

Q: How do I feed the organism from my game?
A: Common patterns:
     engine.interact("jump", intensity=0.5)
     engine.observe("score", value=1200, intensity=0.4)
     engine.push_metric("fps", 0.9)
     engine.pulse(dt)   # once per frame

Q: How do I protect risky functions?
A: Use:
     engine.safe_call(fn, *args, default=0, label="fn_name")
   or decorate with:
     @engine.hook("player_action", default=None)

Q: Why call pulse()?
A: pulse() is the heartbeat: aging, ambient mutation, sensors, emergence
   checks, optional autosave. Without it, time-based life stalls.

Q: How do I keep growth between runs?
A: Pass a state_path and leave auto_load/auto_save on:
     SymbioEngine(name="Wally", state_path="wally_state.json")
   Demo shortcut:
     python examples/minimal_host.py --persist

Q: Can I reset Wally?
A: Delete the state JSON, or boot with force_fresh=True.
   In the console demo, type:  reset

Q: Does save/load restore emergent modules?
A: Yes. Modules re-bind on boot without wiping living meta (bond meters,
   tempo, dream state, etc.).


--------------------------------------------------------------------------------
DEMOS & TROUBLESHOOTING
--------------------------------------------------------------------------------

Q: pygame demo opens then fails / “pygame not installed”
A: Install pygame (`pip install pygame`) or run headless:
     python examples/pygame_integration.py --headless

Q: Headless demo is “too fast” or too short.
A: Change duration:
     python examples/pygame_integration.py --headless --seconds 12

Q: Console demo: unknown command?
A: Type  help  for the command list. Free text is treated as a soft touch.

Q: Tests — how do I run them?
A: From project root:
     python -m unittest tests.test_smoke -v

Q: I see *_state.json files appear. Should I commit them?
A: No. They are local organism checkpoints. .gitignore already excludes them.


--------------------------------------------------------------------------------
CONTRIBUTING & PROJECT
--------------------------------------------------------------------------------

Q: Who is the author?
A: Jonathan Rivera.

Q: What license is it under?
A: MIT — free to use, modify, and distribute commercially; keep the notice.

Q: How can I contribute as a beginner?
A: Improve docs, add an example, propose a new emergent module, or fix a
   small bug. See CONTRIBUTING.md.

Q: Where do I add a new gene cascade?
A: symbio_engine/mutation.py → CASCADE_GRAPH

Q: Where do I add a new emergent module?
A: symbio_engine/emergence.py → EMERGENT_CATALOG

Q: Can I rename the organism?
A: Yes:
     SymbioEngine(name="Ada")

Q: Will this work in multiplayer servers / async apps?
A: The event bus is thread-safe for basic use, but the design targets a
   single host loop (game/script). For heavy concurrency, wrap access or
   give each session its own engine instance.


--------------------------------------------------------------------------------
DESIGN PHILOSOPHY
--------------------------------------------------------------------------------

Q: Why not just use a big neural net?
A: Wally is inspectable, tiny, offline, and fun to embed. You can read the
   genome, memory, and patches. Different tool for a different job.

Q: Why “2041-style” modules?
A: A creative palette — symbiotic, slightly futuristic behaviors that unlock
   like organic features, not a checklist of always-on power-ups.

Q: What’s intentionally out of scope (for now)?
A: Networked multi-organism ecosystems, GUI editor, and LLM brains.
   Those make great extension ideas (see 5-Easy-Ideas-to-Extend.txt).


================================================================================
Still stuck? Open an issue on the GitHub repo with:
  • OS + Python version
  • Exact command you ran
  • Full error text
================================================================================
