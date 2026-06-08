"""
Skills 发现和加载器

演示 Skills 三层加载机制的核心实现：
- Level 1: scan_skills() - 扫描并加载所有 Skills 元数据到 system prompt
- Level 2: load_skill(skill_name: str) - 按名称加载指定 Skill 的详细指令
- Level 3: 由 bash tool 执行脚本（见 tools.py），大模型从指令中自己发现脚本

核心设计理念：让大模型成为真正的"智能体"，自己阅读指令、发现脚本、决定执行。
"""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import yaml

_BUILTIN_SKILLS = Path(__file__).parent / "skills"

DEFAULT_SKILL_PATHS = [
    _BUILTIN_SKILLS,            # 包内内置 skills
    Path.cwd() / ".claude" / "skills",
    Path.cwd() / "skills",
]

_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


@dataclass
class SkillMetadata:
    """Skill 元数据（Level 1）— 从 YAML frontmatter 解析，注入 system prompt"""
    name: str
    description: str
    skill_path: Path

    def to_prompt_line(self) -> str:
        return f"- **{self.name}**: {self.description}"


@dataclass
class SkillContent:
    """Skill 完整内容（Level 2）— 包含 SKILL.md 的完整指令"""
    metadata: SkillMetadata
    instructions: str


def _parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """解析 YAML frontmatter，返回 (metadata_dict, body)。解析失败时 metadata 为 None。"""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        return yaml.safe_load(m.group(1)), text[m.end():].strip()
    except yaml.YAMLError:
        return None, text


class SkillLoader:
    """
    Skills 加载器

    1. scan_skills(): 发现文件系统中的 Skills，解析元数据
    2. load_skill(): 按需加载 Skill 详细内容
    3. build_system_prompt(): 生成包含 Skills 列表的 system prompt
    """

    def __init__(self, skill_paths: list[Path] | None = None):
        self.skill_paths = skill_paths or DEFAULT_SKILL_PATHS
        self._metadata_cache: dict[str, SkillMetadata] = {}
        self._scanned = False

    def scan_skills(self) -> list[SkillMetadata]:
        if self._scanned:
            return list(self._metadata_cache.values())

        for base_path in self.skill_paths:
            if not base_path.is_dir():
                continue
            for skill_dir in base_path.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.is_file():
                    continue
                metadata = self._parse_skill_metadata(skill_md)
                if metadata and metadata.name not in self._metadata_cache:
                    self._metadata_cache[metadata.name] = metadata

        self._scanned = True
        return list(self._metadata_cache.values())

    def invalidate_cache(self):
        """清除扫描缓存，下次 scan_skills() 会重新扫描磁盘"""
        self._metadata_cache.clear()
        self._scanned = False

    def register_skill(self, metadata: SkillMetadata):
        """直接注册一个 Skill 到缓存，无需重新扫描磁盘。
        用于蒸馏完成后立即让 Skill 可被发现。"""
        self._metadata_cache[metadata.name] = metadata
        self._scanned = True

    @staticmethod
    def _parse_skill_metadata(skill_md_path: Path) -> Optional[SkillMetadata]:
        try:
            content = skill_md_path.read_text(encoding="utf-8")
        except Exception:
            return None

        fm, _ = _parse_frontmatter(content)
        if not fm or not fm.get("name"):
            return None

        return SkillMetadata(
            name=fm["name"],
            description=fm.get("description", ""),
            skill_path=skill_md_path.parent,
        )

    def load_skill(self, skill_name: str) -> Optional[SkillContent]:
        metadata = self._metadata_cache.get(skill_name)
        if not metadata:
            if not self._scanned:
                self.scan_skills()
            metadata = self._metadata_cache.get(skill_name)
        if not metadata:
            return None

        skill_md = metadata.skill_path / "SKILL.md"
        try:
            content = skill_md.read_text(encoding="utf-8")
        except Exception:
            return None

        _, instructions = _parse_frontmatter(content)
        return SkillContent(metadata=metadata, instructions=instructions)

    def build_system_prompt(self, base_prompt: str = "") -> str:
        skills = self.scan_skills()

        if not skills:
            skills_section = "## Skills\n\nNo skills currently available.\n"
        else:
            lines = ["## Available Skills\n",
                      "You have access to the following specialized skills:\n"]
            lines.extend(skill.to_prompt_line() for skill in skills)
            lines.append("\n### How to Use Skills\n")
            lines.append("1. **List**: When users ask to list/show/see all skills, use the `list_skills` tool. "
                         "Present the skills in a markdown table format with columns: 序号, 技能名称, 功能描述.\n")
            lines.append("2. **Load**: When a user request matches a skill's description, "
                         "use `load_skill(skill_name)` to get detailed instructions\n")
            lines.append("3. **Execute**: Follow the skill's instructions, which may include "
                         "running scripts via `bash`\n")
            lines.append("\n**Important**:\n")
            lines.append("- Do NOT use glob, bash, or list_dir to search for skill files. "
                         "Use the `list_skills` tool instead.\n")
            lines.append("- Only load a skill when it's relevant to the user's request. "
                         "Script code never enters the context - only their output does.\n")
            skills_section = "\n".join(lines)

        prefix = base_prompt or "You are a helpful coding assistant."
        return f"{prefix}\n\n{skills_section}"


def discover_skills(skill_paths: list[Path] | None = None) -> list[SkillMetadata]:
    loader = SkillLoader(skill_paths)
    return loader.scan_skills()


def get_skill_content(skill_name: str, skill_paths: list[Path] | None = None) -> Optional[SkillContent]:
    loader = SkillLoader(skill_paths)
    return loader.load_skill(skill_name)
