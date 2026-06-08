"""
SKILL.md 合规校验 · 三色灯（ok/warn/error）

完全依据 Anthropic 官方 SKILL.md 规范。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .schemas import Skill

LintLevel = Literal["ok", "warn", "error"]
LintField = Literal["name", "description", "body"]


@dataclass
class LintItem:
    field: LintField
    level: LintLevel
    message: str
    rule: str


RESERVED_WORDS = ["anthropic", "claude", "openai", "skill", "agent"]


def lint_skill(skill: Skill | None) -> list[LintItem]:
    if not skill:
        return []
    items: list[LintItem] = []

    # ─── name ───
    if not skill.name or len(skill.name) == 0:
        items.append(LintItem("name", "error", "name 必填", "name-required"))
    else:
        if len(skill.name) > 64:
            items.append(LintItem("name", "error", f"name 超过 64 字符（当前 {len(skill.name)}）", "name-too-long"))
        if not re.match(r"^[a-z0-9-]+$", skill.name):
            items.append(LintItem("name", "error", "name 必须仅含小写字母/数字/连字符（kebab-case）", "name-format"))
        if skill.name.lower() in RESERVED_WORDS:
            items.append(LintItem("name", "error", f"name 不能用保留词 \"{skill.name}\"", "name-reserved"))
        if len(skill.name) < 4:
            items.append(LintItem("name", "warn", "name 太短，建议 4-30 字符以利于检索", "name-too-short"))

    # ─── description ───
    if not skill.description or len(skill.description) == 0:
        items.append(LintItem("description", "error", "description 必填", "desc-required"))
    else:
        if len(skill.description) > 1024:
            items.append(LintItem("description", "error", f"description 超过 1024 字符（当前 {len(skill.description)}）", "desc-too-long"))
        has_when = bool(re.search(r"(when|use when|适用|用于|何时|场景|trigger|触发|when to|用来|当)", skill.description, re.IGNORECASE))
        if not has_when:
            items.append(LintItem("description", "warn", "description 缺少\"何时使用\"焦点（建议加\"用于：xxx\"或\"适用于：xxx\"）", "desc-missing-when"))
        if "\n" in skill.description:
            items.append(LintItem("description", "warn", "description 单行为佳，多行可能在某些 YAML 解析器出问题", "desc-multiline"))

    # ─── body ───
    if not skill.body or len(skill.body) == 0:
        items.append(LintItem("body", "error", "body 必填", "body-required"))
    else:
        lines = skill.body.count("\n") + 1
        if lines > 500:
            items.append(LintItem("body", "warn", f"body 超过 500 行（当前 {lines}），建议拆分为子 skill", "body-too-long"))
        if not re.search(r"^#\s+", skill.body, re.MULTILINE):
            items.append(LintItem("body", "warn", "body 缺少 H1 标题（# Skill 名称）", "body-no-h1"))

    return items


def lint_level(items: list[LintItem], field: LintField) -> LintLevel:
    field_items = [i for i in items if i.field == field]
    if any(i.level == "error" for i in field_items):
        return "error"
    if any(i.level == "warn" for i in field_items):
        return "warn"
    return "ok"
