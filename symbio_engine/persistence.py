"""Save / load organism state as JSON — survive restarts, grow across sessions."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .organism import Organism
    from .debugger import EvolutionaryDebugger


class Persistence:
    """JSON-based checkpoints for the living organism."""

    def __init__(self, path: Optional[str] = None) -> None:
        if path is None:
            path = os.path.join(os.getcwd(), "symbio_state.json")
        self.path = Path(path)

    def save(
        self,
        organism: "Organism",
        *,
        extra: Optional[Dict[str, Any]] = None,
        debugger: Optional["EvolutionaryDebugger"] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "format": "symbio_engine/v1",
            "saved_at": time.time(),
            "organism": organism.to_dict(),
            "extra": dict(extra or {}),
        }
        if debugger is not None:
            payload["debugger"] = {
                "signatures": dict(debugger.signatures),
                "patches": {
                    pid: {
                        "patch_id": p.patch_id,
                        "signature": p.signature,
                        "strategy": p.strategy,
                        "description": p.description,
                        "created_tick": p.created_tick,
                        "hits": p.hits,
                        "successes": p.successes,
                        "active": p.active,
                        "meta": dict(p.meta),
                    }
                    for pid, p in debugger.patches.items()
                },
                "signature_to_patch": dict(debugger.signature_to_patch),
                "_patch_counter": debugger._patch_counter,
            }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        return str(self.path)

    def load(self) -> Optional[Dict[str, Any]]:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def exists(self) -> bool:
        return self.path.exists()

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
