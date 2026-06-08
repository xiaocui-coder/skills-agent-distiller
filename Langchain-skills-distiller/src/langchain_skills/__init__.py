"""
LangChain Skills Agent + Distiller

融合版：Skills Agent 运行时 + Skill 自动蒸馏/生成能力。
形成"使用 → 发现不足 → 蒸馏新 Skill → 使用"的闭环。

## 核心概念

### Skills 三层加载
- **Level 1 (启动时)**: 扫描 Skills 目录，将元数据注入 system_prompt
- **Level 2 (请求匹配时)**: load_skill 工具读取 SKILL.md 详细指令
- **Level 3 (执行时)**: bash 工具执行脚本，脚本代码不进入上下文

### Distiller 能力
- **distill_skill**: 从对话中蒸馏出 SKILL.md
- **auto_create_skill**: 根据需求描述自动生成完整 Skill
- **lint_skill_content**: 校验 SKILL.md 合规性
- **diff_skill_versions**: 规则级版本对比
- **export_skill**: 多格式导出（Claude Code / ChatGPT / 通用）

## 使用示例

```python
from langchain_skills import LangChainSkillsAgent

# 创建 agent（默认启用 distiller）
agent = LangChainSkillsAgent()

# 对话中 Agent 可自主决定蒸馏新 Skill
result = agent.invoke("帮我把这段对话提炼成一个 Skill")
print(agent.get_last_response(result))

# 或者禁用 distiller（纯 Agent 模式）
agent = LangChainSkillsAgent(enable_distiller=False)
```

## Web API

```bash
# 启动 Web 服务
uv run langchain-skills-distiller-web

# 蒸馏
curl -X POST http://localhost:8000/api/distiller/distill \\
  -H "Content-Type: application/json" \\
  -d '{"input": "...对话内容..."}'

# 自动生成
curl -X POST http://localhost:8000/api/distiller/auto-clarify \\
  -H "Content-Type: application/json" \\
  -d '{"input": "帮我做一个代码审查 Skill"}'
```
"""

from .agent import LangChainSkillsAgent, create_skills_agent
from .skill_loader import SkillLoader, SkillMetadata, SkillContent, discover_skills, get_skill_content
from .tools import load_skill, bash, read_file, write_file, ALL_TOOLS, DISTILLER_TOOLS, SkillAgentContext

__version__ = "0.2.0"

__all__ = [
    # Agent
    "LangChainSkillsAgent",
    "create_skills_agent",
    # Skill Loader
    "SkillLoader",
    "SkillMetadata",
    "SkillContent",
    "discover_skills",
    "get_skill_content",
    # Tools
    "load_skill",
    "bash",
    "read_file",
    "write_file",
    "ALL_TOOLS",
    "DISTILLER_TOOLS",
    # Context
    "SkillAgentContext",
]
