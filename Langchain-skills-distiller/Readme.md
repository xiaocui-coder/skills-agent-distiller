# Langchain-skills-distiller

Skills Agent 运行时 + Skill 自动蒸馏/生成能力。融合自 `src/langchain_skills` 和 `Skill-Distiller-Py` 两个项目。

核心闭环：**使用 Skill → 发现不足 → 蒸馏新 Skill → 立即可用**。

---

## 快速开始

### 前置条件

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) 包管理器（推荐）
- API Key（任选其一）

```bash
# Anthropic Claude（推荐）
export ANTHROPIC_API_KEY=sk-ant-xxx

# 阿里云通义千问
export DASHSCOPE_API_KEY=sk-xxx

# 如需代理
export ANTHROPIC_BASE_URL=https://your-proxy.com
```

### 安装依赖

```bash
cd Langchain-skills-distiller

# 基础安装（CLI 模式）
uv sync

# 含 Web 服务
uv sync --extra web
```

### CLI 模式

```bash
# 列出已发现的 Skills
uv run langchain-skills-distiller --list-skills

# 显示 system prompt
uv run langchain-skills-distiller --show-prompt

# 单次执行
uv run langchain-skills-distiller "列出当前目录的文件"

# 交互式模式（推荐）
uv run langchain-skills-distiller --interactive

# 禁用 Extended Thinking（降低延迟和成本）
uv run langchain-skills-distiller --no-thinking "列出当前目录"

# 指定工作目录
uv run langchain-skills-distiller --cwd /path/to/project --interactive
```

### Web 模式

```bash
# 启动服务（端口 8000）
uv run langchain-skills-distiller-web

# 服务启动后访问
# Agent 对话: ws://localhost:8000/ws/chat
# API 文档:  http://localhost:8000/docs
```

### 作为库调用

```python
from langchain_skills import LangChainSkillsAgent

# 创建 Agent（蒸馏功能默认启用）
agent = LangChainSkillsAgent()

# 正常对话 — Agent 会自主决定何时调用蒸馏工具
result = agent.invoke("帮我整理这些对话规则成一个 Skill")
print(agent.get_last_response(result))

# 纯 Agent 模式（禁用蒸馏）
agent = LangChainSkillsAgent(enable_distiller=False)

# 流式输出
for event in agent.stream_events("帮我写一段公众号开头", thread_id="s1"):
    print(event)
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` | Anthropic API Key | 无（必填其一） |
| `DASHSCOPE_API_KEY` / `QWEN_API_KEY` | 通义千问 API Key | 无（二选一） |
| `ANTHROPIC_BASE_URL` | API 代理地址 | 无 |
| `QWEN_BASE_URL` | 通义千问代理地址 | DashScope 官方 |
| `CLAUDE_MODEL` | 模型名称 | `claude-sonnet-4-20250601` |
| `MAX_TOKENS` | 最大输出 tokens | `16000` |
| `SKILLS_DEBUG` | 调试日志（`1`/`true`） | 关闭 |

---

## 蒸馏功能

### 默认启用

蒸馏功能**默认启用**，无需额外配置。只要 API Key 正确，Agent 创建时会自动初始化 `DistillerEngine`，Agent 在对话中可自主调用 5 个蒸馏工具。

### Agent 蒸馏工具

| 工具 | 功能 | 触发方式 |
|------|------|----------|
| `distill_skill` | 从对话中蒸馏出 SKILL.md | Agent 自动判断，或用户明确要求 |
| `auto_create_skill` | 根据需求描述自动生成完整 Skill | Agent 自动判断，或用户提供需求 |
| `lint_skill_content` | 校验 SKILL.md 是否符合规范 | Agent 自动判断，或用户要求检查 |
| `diff_skill_versions` | 规则级对比两个 Skill 版本 | Agent 自动判断，或用户要求对比 |
| `export_skill` | 导出为 Claude Code / ChatGPT / 通用格式 | Agent 自动判断，或用户要求导出 |

### Skill 自动入库流程

```
用户请求蒸馏
  → Agent 调用 distill_skill 工具
  → DistillerEngine 调用 LLM 生成 SKILL.md
  → 写入 skills/{name}/SKILL.md
  → register_skill() 注入 SkillLoader 缓存
  → 立即可用 load_skill 加载
  → 下次启动自动扫描入库
```

### 禁用蒸馏

```python
# 代码中禁用
agent = LangChainSkillsAgent(enable_distiller=False)
```

---

## Web API

### Agent 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/config` | 模型和功能配置 |
| GET | `/api/skills` | 列出已发现的 Skills |
| GET | `/api/skills/{name}` | 获取 Skill 详细信息 |
| WS | `/ws/chat` | WebSocket 实时对话 |

### Distiller 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/distiller/health` | 蒸馏引擎状态 |
| GET | `/api/distiller/samples` | 列出示例对话场景 |
| GET | `/api/distiller/samples/{key}` | 获取示例对话内容 |
| POST | `/api/distiller/distill` | 流式蒸馏（SSE） |
| POST | `/api/distiller/auto-clarify` | 生成 3 个澄清问题 |
| POST | `/api/distiller/auto-generate` | 流式自动生成（SSE） |
| POST | `/api/distiller/lint` | 校验 SKILL.md |
| POST | `/api/distiller/diff` | 规则级版本对比 |
| POST | `/api/distiller/export` | 格式导出 |
| GET | `/api/distiller/store/skills` | 列出已存储 Skill |
| GET | `/api/distiller/store/skills/{id}` | 查看 Skill 版本历史 |
| DELETE | `/api/distiller/store/skills/{id}` | 删除存储的 Skill |
| GET | `/api/distiller/targets` | 列出导出格式 |

### API 调用示例

```bash
# 蒸馏
curl -X POST http://localhost:8000/api/distiller/distill \
  -H "Content-Type: application/json" \
  -d '{"input": "我：写短句\nAI：在如今数字化时代...\n我：太啰嗦了"}'

# 自动生成（先澄清再生成）
curl -X POST http://localhost:8000/api/distiller/auto-clarify \
  -H "Content-Type: application/json" \
  -d '{"input": "帮我做一个前端代码审查 Skill"}'

curl -X POST http://localhost:8000/api/distiller/auto-generate \
  -H "Content-Type: application/json" \
  -d '{"input": "帮我做一个前端代码审查 Skill", "answers": ["React项目", "TypeScript强类型", "不使用any"]}'

# 校验
curl -X POST http://localhost:8000/api/distiller/lint \
  -H "Content-Type: application/json" \
  -d '{"name": "my-skill", "description": "测试", "body": "## 必须避免\n- 不要用var"}'

# 导出
curl -X POST http://localhost:8000/api/distiller/export \
  -H "Content-Type: application/json" \
  -d '{"skill_name": "my-skill", "target": "chatgpt"}'
```

---

## 核心架构

### Skills 三层加载

| 层级 | 时机 | 实现 |
|------|------|------|
| **Level 1** | 启动时 | `SkillLoader.scan_skills()` 扫描目录，解析 YAML frontmatter，注入 system prompt |
| **Level 2** | 请求匹配时 | `load_skill` 工具读取 SKILL.md 完整指令 |
| **Level 3** | 执行时 | `bash` 工具执行脚本，脚本代码不进入上下文 |

### 流式处理

```
agent.stream_events()
  → LangChain agent.stream(stream_mode="messages")
  → StreamEventEmitter 生成标准化事件
  → ToolCallTracker 追踪工具调用增量 JSON
  → ToolResultFormatter 格式化输出
  → CLI: Rich Live Display / Web: WebSocket JSON
```

### 蒸馏引擎

```
DistillerEngine
  → BaseChatModel.ainvoke()（复用 Agent 的 LLM 实例）
  → 4 个专用 System Prompt（FRESH / ACCUMULATE / CLARIFY / AUTO_GEN）
  → 结构化 JSON 输出解析
  → SKILL.md 写入 + SkillLoader 缓存注册
```

---

## 文件结构

```
Langchain-skills-distiller/
├── pyproject.toml
├── project.md                                # 详细架构文档
└── src/langchain_skills/
    ├── __init__.py
    ├── agent.py                               # Agent 主体（含 DistillerEngine 初始化）
    ├── skill_loader.py                        # 三层加载（新增 register_skill / invalidate_cache）
    ├── tools.py                               # 13 个工具（8 原有 + 5 distiller）
    ├── api_server.py                          # FastAPI 路由（Agent + Distiller 合并）
    ├── cli.py                                 # CLI 交互入口
    ├── web_main.py                            # Uvicorn 入口
    ├── distiller/                             # 蒸馏模块
    │   ├── engine.py                          # 蒸馏引擎（LangChain BaseChatModel）
    │   ├── schemas.py                         # Pydantic 数据模型
    │   ├── prompts.py                         # LLM System Prompts
    │   ├── diff.py                            # 规则级 diff
    │   ├── lint.py                            # SKILL.md 合规校验
    │   ├── store.py                           # JSON 持久化
    │   ├── targets.py                         # 导出格式适配器
    │   └── samples.py                         # 示例对话
    ├── stream/                                # 流式事件管道
    └── memory/                                # 记忆系统
```

---

## 依赖

```
langchain>=1.0.0
langchain-anthropic>=1.0.0
langchain-openai>=1.0.0
langgraph>=1.0.0
pydantic>=2.10.0
prompt-toolkit>=3.0.0
python-dotenv>=1.0
pyyaml>=6.0
rich>=14.2.0

# 可选
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
```
