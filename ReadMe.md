# Skills Agent Distiller

<p align="center">
  <strong>使用技能 → 发现不足 → 蒸馏新技能 → 立即可用</strong>
</p>

<p align="center">
  一个自改进的 AI 技能代理系统，集成 LangChain Agent 运行时、技能自动蒸馏/生成引擎和 React Web 前端。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-1.0-green.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/React-19-61dafb.svg" alt="React">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 特性

- **三层技能加载** — 启动扫描 → 按需加载 → 脚本执行，渐进式注入上下文
- **技能自动蒸馏** — 从对话中提炼模式，自动生成标准 SKILL.md 文件
- **需求驱动生成** — 根据自然语言需求描述，交互式创建完整技能
- **多格式导出** — 支持 Claude Code、ChatGPT、通用 Memory 格式
- **流式交互** — WebSocket 实时推送思考过程、文本、工具调用事件
- **双 LLM 支持** — Anthropic Claude（默认） / 阿里通义千问
- **Web + CLI 双模式** — React 前端界面 或 终端交互式命令行
- **2+ 内置技能** — PDF、日报

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (React 19)                       │
│  Vite + TypeScript + Tailwind CSS + Zustand                 │
│  ┌─────────┐  ┌─────────┐  ┌───────────┐                    │
│  │ /chat   │  │ /skills │  │ /distiller│                    │
│  └────┬────┘  └────┬────┘  └─────┬─────┘                    │
│       │            │             │                           │
│       ▼            ▼             ▼                           │
│   WebSocket     REST API      SSE Stream                     │
└───────┬────────────┬─────────────┬───────────────────────────┘
        │            │             │
        ▼            ▼             ▼
┌──────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + LangGraph)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LangChainSkillsAgent                    │   │
│  │  System Prompt (技能列表) + 13 个工具 + LLM           │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │              SkillLoader (三层加载)                    │   │
│  │  Level 1: 启动扫描 → Level 2: 按需读取 → Level 3:    │   │
│  │  脚本执行                                              │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │              DistillerEngine                          │   │
│  │  对话蒸馏 | 自动生成 | Lint 校验 | Diff 对比 | 导出    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │ Stream 管道   │  │ Memory 系统  │  │ Skill Store    │    │
│  │ Event/Track  │  │ Session/     │  │ JSON 持久化     │    │
│  │ /Formatter   │  │ Persistent   │  │                │    │
│  └──────────────┘  └──────────────┘  └────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   LLM Provider       │
        │  Claude / Qwen       │
        └────────────────────────┘
```

---

## 快速开始

### 前置条件

- Python >= 3.12
- Node.js >= 18
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）
- API Key（任选其一）

### 1. 克隆仓库

```bash
git clone https://github.com/<your-username>/skills-agent-distiller.git
cd skills-agent-distiller
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```bash
# Anthropic Claude（推荐）
ANTHROPIC_AUTH_TOKEN=sk-ant-xxx

# 或阿里云通义千问
DASHSCOPE_API_KEY=sk-xxx

# 模型选择（可选）
CLAUDE_MODEL=claude-sonnet-4-20250601

# API 代理（可选）
ANTHROPIC_BASE_URL=https://your-proxy.com
```

### 3. 启动后端

```bash
cd Langchain-skills-distiller

# 安装 Python 依赖（含 Web 服务）
uv sync --extra web

# 启动 API 服务（端口 8000）
uv run langchain-skills-distiller-web
```

### 4. 启动前端

```bash
cd Frontend

npm install
npm run dev
```

打开浏览器访问 http://localhost:5173

> Vite 开发服务器自动将 `/api` 和 `/ws` 代理到后端 `:8000`，无需额外配置 CORS。

---

## CLI 模式

如果不需要 Web 界面，可以直接使用命令行：

```bash
cd Langchain-skills-distiller
uv sync   # 基础安装即可，无需 --extra web

# 列出已发现的技能
uv run langchain-skills-distiller --list-skills

# 查看系统提示
uv run langchain-skills-distiller --show-prompt

# 单次执行
uv run langchain-skills-distiller "列出当前目录的文件"

# 交互式对话（推荐）
uv run langchain-skills-distiller --interactive

# 指定工作目录
uv run langchain-skills-distiller --cwd /path/to/project --interactive

# 禁用 Extended Thinking（降低延迟和成本）
uv run langchain-skills-distiller --no-thinking "列出当前目录"
```

---

## 作为 Python 库使用

```python
from langchain_skills import LangChainSkillsAgent

# 创建 Agent（蒸馏功能默认启用）
agent = LangChainSkillsAgent()

# 正常对话 — Agent 会自主决定何时调用蒸馏工具
result = agent.invoke("帮我整理这些对话规则成一个 Skill")
print(agent.get_last_response(result))

# 流式输出
for event in agent.stream_events("帮我写一段公众号开头", thread_id="s1"):
    print(event)

# 禁用蒸馏的纯 Agent 模式
agent = LangChainSkillsAgent(enable_distiller=False)
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
| `MAX_TURNS` | 最大对话轮数 | `20` |
| `SKILLS_DEBUG` | 调试日志（`1`/`true`） | 关闭 |
| `PERMISSION_MODE` | 权限模式 | `default` |

---

## 蒸馏引擎

蒸馏功能默认启用，Agent 在对话中可自主调用 5 个蒸馏工具：

| 工具 | 功能 |
|------|------|
| `distill_skill` | 从对话中蒸馏出 SKILL.md |
| `auto_create_skill` | 根据需求描述自动生成完整 Skill |
| `lint_skill_content` | 校验 SKILL.md 是否符合规范 |
| `diff_skill_versions` | 规则级对比两个 Skill 版本 |
| `export_skill` | 导出为 Claude Code / ChatGPT / 通用格式 |

### 蒸馏流程

```
用户请求蒸馏
  → Agent 调用 distill_skill / auto_create_skill
  → DistillerEngine 调用 LLM 生成结构化 SKILL.md
  → 写入 skills/{name}/SKILL.md
  → register_skill() 注入 SkillLoader 缓存（立即可用）
  → lint_skill() 验证合规性
  → 下次启动自动扫描入库
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
| POST | `/api/distiller/distill` | 流式蒸馏（SSE） |
| POST | `/api/distiller/auto-generate` | 流式自动生成（SSE） |
| POST | `/api/distiller/auto-clarify` | 生成 3 个澄清问题 |
| POST | `/api/distiller/lint` | 校验 SKILL.md |
| POST | `/api/distiller/diff` | 规则级版本对比 |
| POST | `/api/distiller/export` | 格式导出 |
| GET | `/api/distiller/store/skills` | 列出已存储 Skill |
| DELETE | `/api/distiller/store/skills/{id}` | 删除存储的 Skill |

启动后访问 http://localhost:8000/docs 查看 Swagger API 文档。

---

## 技术栈

| 层 | 技术 |
|------|------|
| **后端框架** | FastAPI + Uvicorn |
| **Agent** | LangChain 1.0 + LangGraph |
| **LLM** | Anthropic Claude / 阿里通义千问（OpenAI 兼容） |
| **数据模型** | Pydantic v2 |
| **CLI** | Rich + prompt-toolkit |
| **前端** | React 19 + TypeScript 6 |
| **构建工具** | Vite 8 |
| **样式** | Tailwind CSS 4 |
| **状态管理** | Zustand |
| **通信** | WebSocket + SSE + REST |
| **包管理** | uv (Python) / npm (Frontend) |

---

## 项目结构

```
skills-agent-distiller/
├── .env.example                          # 环境变量模板
├── ReadMe.md
│
├── Frontend/                            # React Web 前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                       # 路由：/chat, /skills, /distiller
│       ├── api/                          # REST / WebSocket / SSE 客户端
│       ├── hooks/                        # React hooks
│       ├── stores/                       # Zustand 状态管理
│       ├── components/                   # UI 组件
│       │   ├── chat/                     # 聊天界面
│       │   ├── skills/                   # 技能浏览器
│       │   ├── distiller/                # 蒸馏工作台
│       │   └── layout/                   # 布局组件
│       └── pages/                        # 页面组件
│
├── Langchain-skills-distiller/           # Python 后端
│   ├── pyproject.toml
│   ├── .env                              # 运行时环境配置
│   ├── .claude/skills/                   # 22+ 内置技能（SKILL.md）
│   ├── skills/                           # 用户自定义技能（自动蒸馏写入）
│   └── src/langchain_skills/
│       ├── agent.py                      # Agent 主体
│       ├── skill_loader.py               # 三层技能加载器
│       ├── tools.py                      # 13 个 LangChain 工具
│       ├── api_server.py                 # FastAPI 路由
│       ├── cli.py                        # CLI 入口
│       ├── web_main.py                   # Uvicorn 入口
│       ├── distiller/                    # 蒸馏引擎
│       │   ├── engine.py                 # 核心蒸馏逻辑
│       │   ├── schemas.py               # Pydantic 模型
│       │   ├── prompts.py               # LLM System Prompts
│       │   ├── diff.py                  # 规则级 diff
│       │   ├── lint.py                  # SKILL.md 校验
│       │   ├── store.py                 # JSON 持久化
│       │   ├── targets.py               # 导出格式适配
│       │   └── samples.py              # 示例对话
│       ├── stream/                       # 流式事件管道
│       │   ├── emitter.py              # 事件发射器
│       │   ├── tracker.py              # 工具调用追踪
│       │   └── formatter.py            # 输出格式化
│       └── memory/                       # 记忆系统
│           ├── manager.py               # MemoryManager 门面
│           ├── session.py               # 会话记忆
│           ├── persistent.py            # 持久化记忆
│           └── store.py                # JSON 文件 IO
│
└── .claude/skills/                       # Claude Code 技能
```

---

## License

MIT
