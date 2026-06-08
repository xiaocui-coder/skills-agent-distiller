"""Persistent memory - cross-session storage."""

from datetime import datetime
from typing import Any, Optional

from .store import MemoryStore


class PersistentMemory:
    """Long-term memory with JSON file persistence."""

    def __init__(self, store: MemoryStore):
        self.store = store
        self._items: dict[str, dict[str, Any]] = {}

    def _load(self) -> None:
        data = self.store.load()
        for item in data.get("persistent", []):
            self._items[item["key"]] = item

    def _ensure_loaded(self) -> None:
        if not self._items:
            self._load()

    def get(self, key: str) -> Optional[Any]:
        self._ensure_loaded()
        item = self._items.get(key)
        return item.get("value") if item else None

    def set(self, key: str, value: Any, context: str = "") -> None:
        self._ensure_loaded()
        now = datetime.now().isoformat()
        if key in self._items:
            self._items[key].update({"value": value, "updated_at": now})
        else:
            self._items[key] = {
                "key": key,
                "value": value,
                "created_at": now,
                "updated_at": now,
                "context": context,
            }
        self._save()

    def search(self, query: str) -> list[dict[str, Any]]:
        self._ensure_loaded()
        query_lower = query.lower()
        return [
            item for key, item in self._items.items()
            if query_lower in key.lower() or query_lower in str(item.get("value")).lower()
        ]

    def all(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return list(self._items.values())

    def delete(self, key: str) -> None:
        self._ensure_loaded()
        self._items.pop(key, None)
        self._save()

    def _save(self) -> None:
        data = {
            "persistent": list(self._items.values()),
            "session": {},
        }
        self.store.save(data)