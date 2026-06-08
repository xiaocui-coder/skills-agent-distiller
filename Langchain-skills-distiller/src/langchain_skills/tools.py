"""
LangChain Tools 定义

使用 LangChain 1.0 的 @tool 装器和 ToolRuntime 定义工具：
- 8 个原有工具：load_skill, bash, read_file, write_file, glob, grep, edit, list_dir
- 5 个 distiller 工具：distill_skill, auto_create_skill, lint_skill, diff_skill_versions, export_skill
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from langchain.tools import tool, ToolRuntime

from .skill_loader import SkillLoader
from .stream import resolve_path

_IS_WINDOWS = sys.platform == "win32"

_SKIP_DIRS = frozenset({"node_modules", "__pycache__", ".git", "venv", ".venv"})

_TEST_DIR_RE = re.compile(r"^test\s+-d\s+['\"]?([^'\"]+)['\"]?\s*$")


@dataclass
class SkillAgentContext:
    """Agent 运行时上下文，通过 ToolRuntime[SkillAgentContext] 在 tool 中访问"""
    skill_loader: SkillLoader
    working_directory: Path = field(default_factory=lambda: Path.cwd())
    distiller_engine: Any = None


def _maybe_rewrite_test_dir(command: str, cwd: str) -> str:
    """Windows 下将 `test -d path` 转为 PowerShell Test-Path 命令"""
    if not _IS_WINDOWS:
        return command
    m = _TEST_DIR_RE.match(command.strip())
    if not m:
        return command
    raw = m.group(1).strip()
    abs_path = raw.replace("\\", "/") if os.path.isabs(raw) else os.path.normpath(os.path.join(cwd, raw)).replace("\\", "/")
    ps = f'if (Test-Path -Path "{abs_path}" -PathType Container) {{ exit 0 }} else {{ exit 1 }}'
    return f'powershell -ExecutionPolicy Bypass -NoProfile -Command "{ps}"'


def _format_shell_result(result: subprocess.CompletedProcess) -> str:
    """格式化 subprocess 结果为 [OK]/[FAILED] 前缀的标准输出"""
    parts = [f"[OK]" if result.returncode == 0 else f"[FAILED] Exit code: {result.returncode}", ""]
    if result.stdout:
        parts.append(result.stdout.rstrip())
    if result.stderr:
        if result.stdout:
            parts.append("")
        parts.append("--- stderr ---")
        parts.append(result.stderr.rstrip())
    if not result.stdout and not result.stderr:
        parts.append("(no output)")
    return "\n".join(parts)


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size // 1024}KB"
    return f"{size // (1024 * 1024)}MB"


# ═══════════════════════════════════════════════════════════════════
# 原有工具
# ═══════════════════════════════════════════════════════════════════

@tool
def list_skills(runtime: ToolRuntime[SkillAgentContext]) -> str:
    """List all available skills with their names and descriptions.

    Use this when users ask to list, show, or see all available skills.
    Returns the full list of discovered skills without needing to search files.
    """
    loader = runtime.context.skill_loader
    skills = loader.scan_skills()
    if not skills:
        return "[OK] No skills currently available."

    lines = [f"[OK] Available skills ({len(skills)}):", ""]
    lines.append("| 序号 | 技能名称 | 功能描述 |")
    lines.append("|------|---------|---------|")
    for i, s in enumerate(skills, 1):
        desc = s.description or "No description"
        lines.append(f"| {i} | **{s.name}** | {desc} |")
    return "\n".join(lines)


@tool
def load_skill(skill_name: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Load a skill's detailed instructions.

    This tool reads the SKILL.md file for the specified skill and returns
    its complete instructions. Use this when the user's request matches
    a skill's description from the available skills list.

    Args:
        skill_name: Name of the skill to load (e.g., 'news-extractor')
    """
    loader = runtime.context.skill_loader
    skill_content = loader.load_skill(skill_name)

    if not skill_content:
        skills = loader.scan_skills()
        if skills:
            available = ", ".join(s.name for s in skills)
            return f"Skill '{skill_name}' not found. Available skills: {available}"
        return f"Skill '{skill_name}' not found. No skills are currently available."

    skill_path = skill_content.metadata.skill_path
    scripts_dir = skill_path / "scripts"
    path_info = (
        f"\n## Skill Path Info\n\n"
        f"- **Skill Directory**: `{skill_path}`\n"
        f"- **Scripts Directory**: `{scripts_dir}`\n\n"
        f"**Important**: When running scripts, use absolute paths like:\n"
        f"```bash\nuv run {scripts_dir}/script_name.py [args]\n```\n"
    )
    return f"# Skill: {skill_name}\n\n## Instructions\n\n{skill_content.instructions}\n{path_info}"


@tool
def bash(command: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Execute a shell command (bash on Unix/macOS, cmd.exe on Windows).

    Use this for running skill scripts, installing dependencies, file operations, or any shell command.
    Script code does NOT enter the context, only the output does (Level 3 of Skills loading).

    Args:
        command: The shell command to execute
    """
    cwd = str(runtime.context.working_directory)
    command = _maybe_rewrite_test_dir(command, cwd)

    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=300,
            encoding="utf-8", errors="replace",
        )
        return _format_shell_result(result)
    except subprocess.TimeoutExpired:
        return "[FAILED] Command timed out after 300 seconds."
    except Exception as e:
        return f"[FAILED] {str(e)}"


@tool
def read_file(file_path: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Read the contents of a file with line numbers.

    Args:
        file_path: Path to the file (absolute or relative to working directory)
    """
    path = resolve_path(file_path, runtime.context.working_directory)

    if not path.exists():
        return f"[Error] File not found: {file_path}"
    if not path.is_file():
        return f"[Error] Not a file: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        numbered = [f"{i:4d}| {line}" for i, line in enumerate(lines[:2000], 1)]
        if len(lines) > 2000:
            numbered.append(f"... ({len(lines) - 2000} more lines)")
        return "\n".join(numbered)
    except UnicodeDecodeError:
        return f"[Error] Cannot read file (binary or unknown encoding): {file_path}"
    except Exception as e:
        return f"[Error] Failed to read file: {str(e)}"


@tool
def write_file(file_path: str, content: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Write content to a file. Creates parent directories if needed.

    Args:
        file_path: Path to the file (absolute or relative to working directory)
        content: Content to write
    """
    path = resolve_path(file_path, runtime.context.working_directory)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"[Success] File written: {path}"
    except Exception as e:
        return f"[Error] Failed to write file: {str(e)}"


@tool
def glob(pattern: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Find files matching a glob pattern (e.g., "**/*.py").

    Args:
        pattern: Glob pattern to match files against
    """
    cwd = runtime.context.working_directory
    try:
        matches = sorted(cwd.glob(pattern))
        if not matches:
            return f"No files matching pattern: {pattern}"

        max_results = 100
        result_lines = []
        for p in matches[:max_results]:
            try:
                result_lines.append(str(p.relative_to(cwd)))
            except ValueError:
                result_lines.append(str(p))

        result = "\n".join(result_lines)
        if len(matches) > max_results:
            result += f"\n... and {len(matches) - max_results} more files"
        return f"[OK]\n\n{result}"
    except Exception as e:
        return f"[FAILED] {str(e)}"


@tool
def grep(pattern: str, path: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Search for a regex pattern in files.

    Args:
        pattern: Regular expression pattern to search for
        path: File or directory path to search in (use "." for current directory)
    """
    cwd = runtime.context.working_directory
    search_path = resolve_path(path, cwd)

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"[FAILED] Invalid regex pattern: {e}"

    max_results = 50

    try:
        if search_path.is_file():
            files = [search_path]
        else:
            files = [
                p for p in search_path.rglob("*")
                if p.is_file()
                and not any(part.startswith(".") or part in _SKIP_DIRS for part in p.parts)
            ]
    except Exception as e:
        return f"[FAILED] {str(e)}"

    results = []
    files_searched = 0

    for file_path in files:
        if len(results) >= max_results:
            break
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            files_searched += 1
            for line_num, line in enumerate(content.split("\n"), 1):
                if regex.search(line):
                    try:
                        rel = file_path.relative_to(cwd)
                    except ValueError:
                        rel = file_path
                    results.append(f"{rel}:{line_num}: {line.strip()[:100]}")
                    if len(results) >= max_results:
                        break
        except (UnicodeDecodeError, PermissionError, IsADirectoryError):
            continue

    if not results:
        return f"No matches found for pattern: {pattern} (searched {files_searched} files)"

    output = "\n".join(results)
    if len(results) >= max_results:
        output += f"\n... (truncated, showing first {max_results} matches)"
    return f"[OK]\n\n{output}"


@tool
def edit(
    file_path: str,
    old_string: str,
    new_string: str,
    runtime: ToolRuntime[SkillAgentContext]
) -> str:
    """
    Edit a file by replacing exact text. The old_string must be unique in the file.

    Args:
        file_path: Path to the file to edit
        old_string: The exact text to find and replace
        new_string: The text to replace it with
    """
    path = resolve_path(file_path, runtime.context.working_directory)

    if not path.exists():
        return f"[FAILED] File not found: {file_path}"
    if not path.is_file():
        return f"[FAILED] Not a directory: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)

        if count == 0:
            return "[FAILED] String not found in file. Make sure the text matches exactly including whitespace."
        if count > 1:
            return f"[FAILED] String appears {count} times in file. Please provide more context to make it unique."

        path.write_text(content.replace(old_string, new_string, 1), encoding="utf-8")
        return f"[OK]\n\nEdited {path.name}: replaced {len(old_string.splitlines())} lines with {len(new_string.splitlines())} lines"
    except UnicodeDecodeError:
        return f"[FAILED] Cannot edit file (binary or unknown encoding): {file_path}"
    except Exception as e:
        return f"[FAILED] {str(e)}"


@tool
def list_dir(path: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    List contents of a directory.

    Args:
        path: Directory path (use "." for current directory)
    """
    dir_path = resolve_path(path, runtime.context.working_directory)

    if not dir_path.exists():
        return f"[FAILED] Directory not found: {path}"
    if not dir_path.is_dir():
        return f"[FAILED] Not a directory: {path}"

    try:
        entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines = []
        for entry in entries[:100]:
            if entry.is_dir():
                lines.append(f"  {entry.name}/")
            else:
                lines.append(f"   {entry.name} ({_format_size(entry.stat().st_size)})")
        if len(entries) > 100:
            lines.append(f"... and {len(entries) - 100} more entries")
        return f"[OK]\n\n" + "\n".join(lines)
    except PermissionError:
        return f"[FAILED] Permission denied: {path}"
    except Exception as e:
        return f"[FAILED] {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# 5 个 Distiller 工具
# ═══════════════════════════════════════════════════════════════════

@tool
def distill_skill(
    runtime: ToolRuntime[SkillAgentContext],
    conversation_text: str,
    base_skill_name: str | None = None,
) -> str:
    """从对话中蒸馏出 Skill 定义（SKILL.md）。

    适用于：用户在对话中展示了特定的偏好、工作流程或行为模式，
    希望将其固化为可复用的 Skill。

    如果指定了 base_skill_name，将在已有 Skill 基础上累积升级。

    Args:
        conversation_text: 要蒸馏的对话文本
        base_skill_name: 可选，已有 Skill 名称，用于累积升级
    """
    import asyncio
    from .distiller.targets import to_claude_code_md
    from .distiller.lint import lint_skill as do_lint

    engine = runtime.context.distiller_engine
    if not engine:
        return "[FAILED] Distiller engine not initialized"

    base_skill = None
    if base_skill_name:
        content = runtime.context.skill_loader.load_skill(base_skill_name)
        if not content:
            return f"[FAILED] Base skill '{base_skill_name}' not found"
        base_skill = {
            "name": content.metadata.name,
            "description": content.metadata.description,
            "body": content.instructions,
            "version": 1,
        }

    try:
        result = asyncio.get_event_loop().run_until_complete(
            engine.distill(conversation_text, base_skill)
        )
    except RuntimeError:
        result = asyncio.run(engine.distill(conversation_text, base_skill))

    skill = result.skill
    skill_dir = runtime.context.working_directory / "skills" / skill.name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md_content = to_claude_code_md(skill)
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    # 注册到 SkillLoader 缓存
    from .skill_loader import SkillMetadata
    metadata = SkillMetadata(
        name=skill.name,
        description=skill.description,
        skill_path=skill_dir,
    )
    runtime.context.skill_loader.register_skill(metadata)

    # 如果有 reference（auto_generate 场景），也写入
    summary_lines = [
        f"[OK] Skill '{skill.name}' has been created and registered.",
        "",
        "## Skill Summary",
        f"- **Name**: {skill.name}",
        f"- **Description**: {skill.description}",
        f"- **Location**: {skill_dir}",
        f"- **Signals extracted**: {len(result.signals)}",
    ]

    # Lint 检查
    lint_items = do_lint(skill)
    if lint_items:
        errors = [i for i in lint_items if i.level == "error"]
        warns = [i for i in lint_items if i.level == "warn"]
        if errors or warns:
            summary_lines.append("")
            summary_lines.append("## Lint Results")
            for item in lint_items:
                icon = "ERROR" if item.level == "error" else "WARN"
                summary_lines.append(f"  [{icon}] {item.field}: {item.message}")
    else:
        summary_lines.append("- **Lint**: passed all checks")

    summary_lines.append("")
    summary_lines.append(
        f"This skill is now available. Use `load_skill('{skill.name}')` "
        f"to load its full instructions at any time."
    )

    return "\n".join(summary_lines)


@tool
def auto_create_skill(
    runtime: ToolRuntime[SkillAgentContext],
    requirement: str,
    answers: list[str] | None = None,
) -> str:
    """根据需求描述自动创建一个完整的 Skill（SKILL.md + reference.md）。

    适用于：用户提供了一个技能需求，希望一键生成完整的 Skill 定义。

    Args:
        requirement: 技能需求描述
        answers: 可选，澄清问题的回答列表
    """
    import asyncio
    from .distiller.targets import to_claude_code_md
    from .distiller.lint import lint_skill as do_lint

    engine = runtime.context.distiller_engine
    if not engine:
        return "[FAILED] Distiller engine not initialized"

    try:
        result = asyncio.get_event_loop().run_until_complete(
            engine.auto_generate(requirement, answers)
        )
    except RuntimeError:
        result = asyncio.run(engine.auto_generate(requirement, answers))

    skill = result.skill
    skill_dir = runtime.context.working_directory / "skills" / skill.name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # 写入 SKILL.md
    skill_md_content = to_claude_code_md(skill)
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    # 写入 reference.md
    ref = result.reference
    ref_lines = [f"# {ref.title}", ""]
    for section in ref.sections:
        ref_lines.append(f"## {section.heading}")
        ref_lines.append("")
        ref_lines.append(section.content)
        ref_lines.append("")
    (skill_dir / "reference.md").write_text("\n".join(ref_lines), encoding="utf-8")

    # 注册到 SkillLoader 缓存
    from .skill_loader import SkillMetadata
    metadata = SkillMetadata(
        name=skill.name,
        description=skill.description,
        skill_path=skill_dir,
    )
    runtime.context.skill_loader.register_skill(metadata)

    summary_lines = [
        f"[OK] Skill '{skill.name}' auto-generated and registered.",
        "",
        "## Intent Analysis",
        f"- **Domain**: {result.intent.domain}",
        f"- **Primary Task**: {result.intent.primary_task}",
        f"- **Triggers**: {', '.join(result.intent.triggers)}",
        f"- **Audience**: {result.intent.audience}",
        "",
        "## Generated Files",
        f"- `{skill_dir}/SKILL.md`",
        f"- `{skill_dir}/reference.md`",
    ]

    lint_items = do_lint(skill)
    if lint_items:
        summary_lines.append("")
        summary_lines.append("## Lint Results")
        for item in lint_items:
            icon = "ERROR" if item.level == "error" else "WARN"
            summary_lines.append(f"  [{icon}] {item.field}: {item.message}")
    else:
        summary_lines.append("")
        summary_lines.append("- **Lint**: passed all checks")

    summary_lines.append("")
    summary_lines.append(
        f"Use `load_skill('{skill.name}')` to load its instructions."
    )

    return "\n".join(summary_lines)


@tool
def lint_skill_content(
    content: str,
) -> str:
    """检查 SKILL.md body 内容是否符合 Anthropic 官方规范。

    检查项包括：命名格式、描述质量、正文结构等。

    Args:
        content: SKILL.md 的 body 内容（Markdown 格式）
    """
    from .distiller.schemas import Skill
    from .distiller.lint import lint_skill as do_lint

    skill = Skill(name="temp-check", description="temporary skill for lint check", body=content)
    items = do_lint(skill)

    if not items:
        return "[OK] Skill passes all lint checks."

    lines = [f"[OK] Lint results ({len(items)} items):", ""]
    for item in items:
        icon = "ERROR" if item.level == "error" else "WARN"
        lines.append(f"  [{icon}] {item.field}: {item.message}")
        lines.append(f"         rule: {item.rule}")
    return "\n".join(lines)


@tool
def diff_skill_versions(
    old_body: str,
    new_body: str,
) -> str:
    """比较两个 Skill 版本的规则级差异。

    解析两个 SKILL.md body 为规则条目，做集合 diff（非行级 LCS），
    更适合人类审阅。

    Args:
        old_body: 旧版 SKILL.md 的 body 内容
        new_body: 新版 SKILL.md 的 body 内容
    """
    from .distiller.diff import diff_rules

    result = diff_rules(old_body, new_body)

    lines = [f"[OK] Rule-level diff:", ""]

    if result.added:
        lines.append(f"### Added ({len(result.added)} rules)")
        for r in result.added:
            lines.append(f"  + [{r.section}] {r.text}")
        lines.append("")

    if result.removed:
        lines.append(f"### Removed ({len(result.removed)} rules)")
        for r in result.removed:
            lines.append(f"  - [{r.section}] {r.text}")
        lines.append("")

    if result.kept:
        lines.append(f"### Kept ({len(result.kept)} rules)")
        for r in result.kept:
            lines.append(f"  = [{r.section}] {r.text}")

    if not result.added and not result.removed:
        lines.append("No changes detected. Both versions have identical rules.")

    return "\n".join(lines)


@tool
def export_skill(
    runtime: ToolRuntime[SkillAgentContext],
    skill_name: str,
    target: str = "claude-code",
) -> str:
    """将已有 Skill 导出为不同格式。

    支持的目标格式：
    - claude-code: 完整 SKILL.md（含 YAML frontmatter），适用于 Claude Code
    - chatgpt: Custom Instructions 格式，适用于 ChatGPT
    - memory: 轻量版（5 条要点），适用于任何 AI 系统消息

    Args:
        skill_name: 要导出的 Skill 名称
        target: 目标格式（claude-code / chatgpt / memory）
    """
    from .distiller.schemas import Skill
    from .distiller.targets import TARGETS, to_claude_code_md, to_chatgpt_instructions, to_memory_short

    content = runtime.context.skill_loader.load_skill(skill_name)
    if not content:
        return f"[FAILED] Skill '{skill_name}' not found"

    skill = Skill(
        name=content.metadata.name,
        description=content.metadata.description,
        body=content.instructions,
    )

    export_map = {
        "claude-code": to_claude_code_md,
        "chatgpt": to_chatgpt_instructions,
        "memory": to_memory_short,
    }

    if target not in export_map:
        available = ", ".join(export_map.keys())
        return f"[FAILED] Unknown target '{target}'. Available: {available}"

    exported = export_map[target](skill)

    lines = [
        f"[OK] Exported '{skill_name}' as '{target}' format.",
        "",
        "## Exported Content",
        "",
        "---",
        exported,
        "---",
    ]

    target_info = next((t for t in TARGETS if t.key == target), None)
    if target_info:
        lines.append("")
        lines.append(f"**Hint**: {target_info.hint}")

    return "\n".join(lines)


ALL_TOOLS = [
    list_skills, load_skill, bash, read_file, write_file, glob, grep, edit, list_dir,
    distill_skill, auto_create_skill, lint_skill_content, diff_skill_versions, export_skill,
]

DISTILLER_TOOLS = [distill_skill, auto_create_skill, lint_skill_content, diff_skill_versions, export_skill]
