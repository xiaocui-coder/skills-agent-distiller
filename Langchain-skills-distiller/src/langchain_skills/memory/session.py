"""Session memory - only valid for current session."""

from typing import Any


class SessionMemory:
    """In-memory session storage, cleared on session end."""

    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self._items: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._items.get(key)

    def set(self, key: str, value: Any) -> None:
        self._items[key] = value

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

    def all(self) -> dict[str, Any]:
        return self._items.copy()

    def clear(self) -> None:
        self._items.clear()