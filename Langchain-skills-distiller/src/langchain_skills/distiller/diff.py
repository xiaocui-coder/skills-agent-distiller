"""
SKILL.md body 的规则级 diff

把 body 解析成"规则条目"（## 段落 + 每行 - / * 列表项），
然后做集合 diff（不是行级 LCS）—— 更适合给非工程师看。
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SkillRule:
    section: str
    text: str
    raw: str


def _norm(s: str) -> str:
    return re.sub(r"[\s,，。.!！?？]+", "", s.strip().lower())


def parse_rules(body: str | None) -> list[SkillRule]:
    if not body:
        return []
    lines = body.split("\n")
    rules: list[SkillRule] = []
    current_section = ""
    for line in lines:
        h2 = re.match(r"^##\s+(.+)$", line)
        if h2:
            current_section = re.sub(r"[（(].*?[)）]\s*$", "", h2.group(1)).strip()
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet:
            text = bullet.group(1).strip()
            if text:
                rules.append(SkillRule(section=current_section, text=text, raw=line))
    return rules


@dataclass
class RuleDiff:
    added: list[SkillRule]
    removed: list[SkillRule]
    kept: list[SkillRule]


def diff_rules(old_body: str | None, new_body: str) -> RuleDiff:
    """规则级 diff · 比较 v1 / v2 的规则集合"""
    old_rules = parse_rules(old_body)
    new_rules = parse_rules(new_body)

    old_norms = {_norm(r.text) for r in old_rules}
    new_norms = {_norm(r.text) for r in new_rules}

    return RuleDiff(
        added=[r for r in new_rules if _norm(r.text) not in old_norms],
        removed=[r for r in old_rules if _norm(r.text) not in new_norms],
        kept=[r for r in new_rules if _norm(r.text) in old_norms],
    )


# ─── line-based diff（兼容旧接口）───────────────

@dataclass
class DiffLine:
    kind: str   # "added" | "removed" | "kept"
    text: str
    index: int


@dataclass
class DiffStats:
    added: int
    removed: int
    kept: int
    old_total: int
    new_total: int


@dataclass
class BodyDiff:
    new_lines: list[DiffLine]
    removed_lines: list[DiffLine]
    stats: DiffStats


def diff_skill_body(old_text: str | None, new_text: str) -> BodyDiff:
    old_lines = (old_text or "").split("\n")
    new_lines = new_text.split("\n")

    old_set = {l.strip() for l in old_lines if l.strip()}
    new_set = {l.strip() for l in new_lines if l.strip()}

    new_diff = []
    for i, text in enumerate(new_lines):
        t = text.strip()
        if not t:
            new_diff.append(DiffLine("kept", text, i))
        else:
            new_diff.append(DiffLine("added" if t not in old_set else "kept", text, i))

    removed_diff = []
    for i, text in enumerate(old_lines):
        t = text.strip()
        if t and t not in new_set:
            removed_diff.append(DiffLine("removed", text, i))

    return BodyDiff(
        new_lines=new_diff,
        removed_lines=removed_diff,
        stats=DiffStats(
            added=sum(1 for l in new_diff if l.kind == "added"),
            removed=len(removed_diff),
            kept=sum(1 for l in new_diff if l.kind == "kept" and l.text.strip()),
            old_total=len(old_set),
            new_total=len(new_set),
        ),
    )
