"""JSON-file persistence layer — mirrors the Univer headless store."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol

DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".univer_data"
)
DEFAULT_FILE_NAME = "store.json"


class Persistence(Protocol):
    """Interface that any persistence backend must implement."""

    def save(self, state: dict[str, Any]) -> None: ...

    def load(self) -> dict[str, Any] | None: ...


class JsonFilePersistence:
    """Persists FUniver state as a single JSON file."""

    def __init__(self, data_dir: str | None = None, filename: str = DEFAULT_FILE_NAME) -> None:
        self._path = Path(data_dir or DEFAULT_DATA_DIR) / filename
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: dict[str, Any]) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise PersistenceError(f"Failed to write state to {self._path}: {exc}") from exc

    def load(self) -> dict[str, Any] | None:
        if not self._path.exists():
            return None
        try:
            with open(self._path, encoding="utf-8") as f:
                state = json.load(f)
        except json.JSONDecodeError as exc:
            raise PersistenceError(f"Corrupted state file {self._path}: {exc}") from exc
        except OSError as exc:
            raise PersistenceError(f"Failed to read state from {self._path}: {exc}") from exc
        return state if isinstance(state, dict) else None


class PersistenceError(RuntimeError):
    """Raised when the persistence layer cannot complete an operation."""
