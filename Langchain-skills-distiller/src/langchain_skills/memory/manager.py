"""Memory manager - unified interface."""

from pathlib import Path
from typing import Any, Optional

from .store import MemoryStore
from .session import SessionMemory
from .persistent import PersistentMemory


class MemoryManager:
    """Unified memory interface with session + persistent storage."""

    AUTO_RECALL_KEYWORDS = ["之前", "上次", "记得", "偏好", "用户"]

    def __init__(self, working_directory: Path):
        storage_path = working_directory / ".claude" / "memory"
        self.store = MemoryStore(storage_path)
        self.session: Optional[SessionMemory] = None
        self.persistent = PersistentMemory(self.store)

    def start_session(self, thread_id: str) -> None:
        """Start a new session."""
        self.session = SessionMemory(thread_id)

    def end_session(self) -> None:
        """End current session and clear session memory."""
        if self.session:
            self.session.clear()
            self.session = None

    def memorize(
        self, key: str, value: Any, scope: str = "session", context: str = ""
    ) -> str:
        """Store memory."""
        if scope == "persistent":
            self.persistent.set(key, value, context)
            return f"[OK] Stored persistent memory: {key}"
        if self.session:
            self.session.set(key, value)
            return f"[OK] Stored session memory: {key}"
        return f"[FAILED] No active session"

    def recall(self, query: str = "", key: str = "") -> str:
        """Recall memory."""
        # exact key lookup
        if key:
            val = self.session.get(key) if self.session else None
            if val is not None:
                return f"{key}: {val}"
            val = self.persistent.get(key)
            if val is not None:
                return f"{key}: {val}"
            return f"[FAILED] Key not found: {key}"

        # search
        if query:
            if not self._should_recall(query):
                return ""

            results = []
            # session
            if self.session:
                for k, v in self.session.all().items():
                    if query.lower() in k.lower():
                        results.append(f"session:{k}: {v}")

            # persistent
            for item in self.persistent.search(query):
                results.append(f"persistent:{item['key']}: {item['value']}")

            if results:
                return "[OK]\n\n" + "\n".join(results)
            return "[OK] No relevant memories found."

        return "[FAILED] Provide query or key"

    def _should_recall(self, query: str) -> bool:
        """Check if should trigger recall."""
        return any(kw in query.lower() for kw in self.AUTO_RECALL_KEYWORDS)

    def get_prompt_injection(self) -> str:
        """Get prompt injection for Level 1."""
        return """
## Memory System
- Use `remember(key, value, scope)` to store memory
- Use `recall(query, key)` to recall memory
- scope: "session" (current only) or "persistent" (cross-session)
"""