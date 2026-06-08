"""Memory storage - JSON file persistence."""

import json
from pathlib import Path
from typing import Any, Optional


class MemoryStore:
    """Simple JSON file storage for memories."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._file = storage_path / "memories.json"

    def load(self) -> dict[str, Any]:
        """Load all memories from file."""
        if self._file.exists():
            return json.loads(self._file.read_text(encoding="utf-8"))
        return {"persistent": [], "session": {}}

    def save(self, data: dict[str, Any]) -> None:
        """Save all memories to file."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )