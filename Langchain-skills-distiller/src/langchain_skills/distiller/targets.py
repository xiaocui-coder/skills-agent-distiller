"""
把 SKILL.md 转换为不同 AI 工具的"粘贴格式"
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import Skill


def to_claude_code_md(skill: Skill) -> str:
    return f"""---
name: {skill.name}
description: {skill.description}
---

{skill.body}
"""


def to_chatgpt_instructions(skill: Skill) -> str:
    return f"""# {skill.name}

{skill.description}

---

{skill.body}"""


def to_memory_short(skill: Skill) -> str:
    bullets = []
    for line in skill.body.split("\n"):
        if re.match(r"^\s*[-*]", line):
            bullets.append(line.strip())
        if len(bullets) >= 5:
            break
    bullet_text = "\n".join(bullets)

    return f"""{skill.description}

要点：
{bullet_text or skill.body[:200] + "..."}"""


@dataclass
class TargetOption:
    key: str
    emoji: str
    title: str
    filename: str
    description: str
    hint: str
    generate: callable


TARGETS: list[TargetOption] = [
    TargetOption(
        key="claude-code",
        emoji="\U0001f916",
        title="给 Claude Code",
        filename="SKILL.md",
        description="完整 SKILL.md 文件 · 含 YAML frontmatter",
        hint="下载后放到 ~/.claude/skills/{name}/SKILL.md",
        generate=to_claude_code_md,
    ),
    TargetOption(
        key="chatgpt",
        emoji="\U0001f4ac",
        title="给 ChatGPT",
        filename="custom-instructions.md",
        description="Custom Instructions 适配版（去掉 YAML）",
        hint="复制粘贴到 Settings → Personalization → Custom Instructions",
        generate=to_chatgpt_instructions,
    ),
    TargetOption(
        key="memory",
        emoji="\U0001f9e0",
        title="通用轻量版",
        filename="memory-short.txt",
        description="提炼 5 条核心要点 · 任何 AI 系统消息可用",
        hint="贴在任何对话开头，让 AI 立即遵守",
        generate=to_memory_short,
    ),
]
