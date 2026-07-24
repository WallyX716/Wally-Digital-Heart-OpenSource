"""
SymbioEngine — a lightweight living digital organism for any Python program.

Import, attach hooks, and let the engine grow from user interactions and
runtime data: butterfly-effect mutations, self-healing, evolutionary patches,
and 2041-style emergent behaviors.
"""

from .engine import SymbioEngine
from .hooks import symbio_hook, on_event, host_callback
from .events import EventBus
from .organism import Organism

__version__ = "0.1.1"
__all__ = [
    "SymbioEngine",
    "Organism",
    "EventBus",
    "symbio_hook",
    "on_event",
    "host_callback",
    "__version__",
]
