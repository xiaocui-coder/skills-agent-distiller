"""
状态管理 · JSON 文件持久化

SavedSkill 是一个 lineage（演化谱系）—— 同一个 skill 名下多个版本。
存储路径：~/.langchain_skills/distiller/store.json
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .schemas import DistillResult

Stage = Literal["idle", "signals", "clusters", "mapping", "skill", "lint", "done"]
DistillMode = Literal["fresh", "accumulate"]
SkillSource = Literal["distilled", "auto-generated"]


@dataclass
class SkillVersion:
    v: int
    description: str
    body: str
    signal_count: int
    added_conversation: str
    created_at: float


@dataclass
class SavedSkill:
    id: str
    name: str
    scenario: str | None = None
    source: SkillSource = "distilled"
    versions: list[SkillVersion] = field(default_factory=list)
    created_at: float = 0.0

    def __post_init__(self):
        if self.versions and self.created_at == 0.0:
            self.created_at = self.versions[0].created_at


def get_latest_version(s: SavedSkill) -> SkillVersion:
    return s.versions[-1]


def get_total_signals(s: SavedSkill) -> int:
    return sum(v.signal_count for v in s.versions)


def get_total_conversations(s: SavedSkill) -> int:
    return len(s.versions)


@dataclass
class SessionState:
    """当前会话状态（不持久化）"""
    input_text: str = ""
    scenario: str | None = None
    stage: Stage = "idle"
    result: DistillResult | None = None
    error: str | None = None
    mode: DistillMode = "fresh"
    base_skill_id: str | None = None


class SkillStore:
    """持久化 Skill 库管理"""

    MAX_SKILLS = 50
    CONVERSATION_MAX_LEN = 500

    def __init__(self, store_path: Path | None = None):
        if store_path:
            self._path = store_path
        else:
            self._path = Path.home() / ".langchain_skills" / "distiller" / "store.json"
        self._library: list[SavedSkill] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            library_data = data.get("library", [])
            self._library = []
            for item in library_data:
                versions = [
                    SkillVersion(
                        v=v["v"],
                        description=v["description"],
                        body=v["body"],
                        signal_count=v["signal_count"],
                        added_conversation=v["added_conversation"],
                        created_at=v["created_at"],
                    )
                    for v in item.get("versions", [])
                ]
                skill = SavedSkill(
                    id=item["id"],
                    name=item["name"],
                    scenario=item.get("scenario"),
                    source=item.get("source", "distilled"),
                    versions=versions,
                    created_at=item.get("created_at", versions[0].created_at if versions else 0.0),
                )
                self._library.append(skill)
        except (json.JSONDecodeError, KeyError, TypeError, IndexError):
            self._library = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "library": [
                {
                    "id": s.id,
                    "name": s.name,
                    "scenario": s.scenario,
                    "source": s.source,
                    "versions": [
                        {
                            "v": v.v,
                            "description": v.description,
                            "body": v.body,
                            "signal_count": v.signal_count,
                            "added_conversation": v.added_conversation,
                            "created_at": v.created_at,
                        }
                        for v in s.versions
                    ],
                    "created_at": s.created_at,
                }
                for s in self._library
            ]
        }
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @property
    def library(self) -> list[SavedSkill]:
        return list(self._library)

    def create_skill(
        self,
        name: str,
        description: str,
        body: str,
        signal_count: int,
        added_conversation: str,
        scenario: str | None = None,
        source: SkillSource = "distilled",
    ) -> str:
        """创建新 lineage（v1）·返回新 skill 的 id"""
        skill_id = f"{name}-{int(time.time() * 1000)}"
        now = time.time()
        skill = SavedSkill(
            id=skill_id,
            name=name,
            scenario=scenario,
            source=source,
            versions=[
                SkillVersion(
                    v=1,
                    description=description,
                    body=body,
                    signal_count=signal_count,
                    added_conversation=added_conversation[: self.CONVERSATION_MAX_LEN],
                    created_at=now,
                )
            ],
            created_at=now,
        )
        self._library = [skill] + self._library
        self._library = self._library[: self.MAX_SKILLS]
        self._save()
        return skill_id

    def append_version(
        self,
        id: str,
        description: str,
        body: str,
        signal_count: int,
        added_conversation: str,
    ) -> None:
        """在已有 lineage 上追加新版本（v2/v3...）"""
        for s in self._library:
            if s.id == id:
                next_v = (s.versions[-1].v if s.versions else 0) + 1
                s.versions.append(
                    SkillVersion(
                        v=next_v,
                        description=description,
                        body=body,
                        signal_count=signal_count,
                        added_conversation=added_conversation[: self.CONVERSATION_MAX_LEN],
                        created_at=time.time(),
                    )
                )
                self._save()
                return

    def get_skill(self, id: str) -> SavedSkill | None:
        for s in self._library:
            if s.id == id:
                return s
        return None

    def remove_skill(self, id: str) -> None:
        self._library = [s for s in self._library if s.id != id]
        self._save()

    def clear_library(self) -> None:
        self._library = []
        self._save()
