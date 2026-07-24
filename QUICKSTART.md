================================================================================
Wally Digital Heart · Quick-Start Guide
Fastest path from zero → “wow, it’s alive”
By Jonathan
================================================================================

Goal: in under 5 minutes, run the heart of the project and feel the core value —
a digital organism that reacts, heals, and grows.


--------------------------------------------------------------------------------
STEP 0 — Open the project folder
--------------------------------------------------------------------------------

On your machine the open-source copy is:

  Desktop → Wally-Digital-Heart-OpenSource

Open a terminal *in that folder*.

Windows PowerShell example:

  cd "$env:USERPROFILE\OneDrive\Desktop\Wally-Digital-Heart-OpenSource"

(If Desktop is not under OneDrive, drop the OneDrive part.)


--------------------------------------------------------------------------------
STEP 1 — Confirm Python works
--------------------------------------------------------------------------------

  python --version

You want 3.9 or higher. If `python` fails, try `py --version`.


--------------------------------------------------------------------------------
STEP 2 — Run the 60-second demo (core value)
--------------------------------------------------------------------------------

  python examples/minimal_host.py

What you’re watching:
  • Wally boots with a small genome
  • Host “work” ticks feed the organism
  • Deliberate divide-by-zero errors are self-healed
  • Complexity rises; an emergent module may awaken
  • A narrative portrait prints before and after

This is the product’s promise in one command: attach → pulse → grow.


--------------------------------------------------------------------------------
STEP 3 — See self-healing & evolution (2 minutes)
--------------------------------------------------------------------------------

  python examples/self_heal_lab.py

Watch for:
  • Healed division by zero
  • flaky(even) → safe default after learning
  • flaky(odd)  → still returns real results (patches don’t kill good paths)
  • An invented patch id like P0001 [return_default]


--------------------------------------------------------------------------------
STEP 4 — Feel a game loop (optional, 1–2 minutes)
--------------------------------------------------------------------------------

No pygame needed:

  python examples/pygame_integration.py --headless --seconds 6

With a window (optional):

  pip install pygame
  python examples/pygame_integration.py

Controls in the window:
  click = interact · space = touch · e = error · s = success · esc = quit


--------------------------------------------------------------------------------
STEP 5 — Pet Wally in the console (optional, fun)
--------------------------------------------------------------------------------

  python examples/console_life.py

Then type:

  t hand
  s
  p 15
  story
  quit


--------------------------------------------------------------------------------
STEP 6 — Drop it into YOUR script (copy-paste)
--------------------------------------------------------------------------------

  from symbio_engine import SymbioEngine

  engine = SymbioEngine(name="Wally").boot()

  engine.interact("hello", intensity=0.6)
  engine.observe("score", value=10, intensity=0.4)
  print(engine.pulse(0.1))
  print(engine.narrative())

  engine.shutdown()

If you didn’t pip-install the package, keep this at the top of your file
(adjust the path to wherever the project folder lives):

  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(r"PATH_TO_Wally-Digital-Heart-OpenSource")))


--------------------------------------------------------------------------------
STEP 7 — Grow across days (optional)
--------------------------------------------------------------------------------

  python examples/minimal_host.py --persist

State is saved under examples/ as JSON. Don’t commit those files to git —
they’re personal sessions.


--------------------------------------------------------------------------------
SUCCESS CHECKLIST
--------------------------------------------------------------------------------

[ ] minimal_host.py ran without errors
[ ] You saw health / mood / complexity numbers
[ ] self_heal_lab showed a healed failure and a patch
[ ] You understand: interact/observe → pulse → narrative

You’re ready. For GitHub publishing see Open-Source-to-GitHub-Guide.txt.
For ideas, see 5-Easy-Ideas-to-Extend.txt. For questions, FAQ-and-Q&A.txt.


--------------------------------------------------------------------------------
ONE-SCREEN CHEAT SHEET
--------------------------------------------------------------------------------

  cd Wally-Digital-Heart-OpenSource
  python examples/minimal_host.py
  python examples/self_heal_lab.py
  python examples/pygame_integration.py --headless
  python examples/console_life.py

Core API:

  engine = SymbioEngine(name="Wally").boot()
  engine.interact("touch")
  engine.safe_call(risky_fn, *args, default=None, label="risky_fn")
  info = engine.pulse(dt)
  engine.shutdown()

================================================================================
