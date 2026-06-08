# Langchain-skills-distiller

Skills Agent 运行时 + Skill 自动蒸馏/生成能力。融合自 `src/langchain_skills` 和 `Skill-Distiller-Py` 两个项目。

核心闭环：**使用 Skill → 发现不足 → 蒸馏新 Skill → 立即可用**。

---

## 文件架构

```
Langchain-skills-distiller/
├── pyproject.toml                              # 包配置，新增依赖 pydantic>=2.10.0
└── src/langchain_skills/
    ├── __init__.py                              # 包导出，版本 v0.2.0
    ├── agent.py                                 # Agent 主体（扩展版）
    ├── skill_loader.py                          # Skill 发现加载器（扩展版）
    ├── tools.py                                 # 工具定义（8 原有 + 5 新增）
    ├── api_server.py                            # FastAPI 路由（合并版）
    ├── web_main.py                              # Uvicorn 入口
    ├── cli.py                                   # CLI 交互入口
    ├── distiller/                               # 蒸馏模块（从 Skill-Distiller-Py 迁移）
    │   ├── __init__.py                          # 模块导出
    │   ├── schemas.py                           # Pydantic 数据模型
    │   ├── prompts.py                           # LLM System Prompts
    │   ├── engine.py                            # 蒸馏引擎（核心新增）
    │   ├── diff.py                              # 规则级 diff
    │   ├── lint.py                              # SKILL.md 合规校验
    │   ├── store.py                             # JSON 持久化
    │   ├── targets.py                           # 导出格式适配器
    │   └── samples.py                           # 示例对话场景
    ├── stream/                                  # 流式事件管道
    │   ├── __init__.py
    │   ├── emitter.py                           # StreamEventEmitter 事件工厂
    │   ├── tracker.py                           # ToolCallTracker 增量 JSON 追踪
    │   ├── formatter.py                         # ToolResultFormatter 输出格式化
    │   └── utils.py                             # 常量与工具函数
    └── memory/                                  # 记忆系统
        ├── __init__.py
        ├── manager.py                           # MemoryManager 统一门面
        ├── session.py                           # SessionMemory 会话级
        ├── persistent.py                        # PersistentMemory 持久化
        └── store.py                             # MemoryStore JSON 文件 IO
```

---

## 各文件职责

### 顶层模块

| 文件 | 行数 | 来源 | 职责 |
|------|------|------|------|
| `agent.py` | 384 | 原有 + 扩展 | Agent 主体，初始化 LLM、SkillLoader、DistillerEngine，编排流式事件 |
| `skill_loader.py` | 166 | 原有 + 扩展 | 三层 Skill 发现加载，新增 `register_skill()` 和 `invalidate_cache()` |
| `tools.py` | 670 | 原有 + 扩展 | 13 个 LangChain @tool 定义，`SkillAgentContext` 扩展了 `distiller_engine` 字段 |
| `api_server.py` | 421 | 原有 + 扩展 | FastAPI 路由，合并 Agent 路由和 Distiller 路由 |
| `cli.py` | 775 | 原样迁移 | argparse CLI，Rich Live 流式渲染 |
| `web_main.py` | 16 | 新增 | Uvicorn 启动入口，port 8000 |

### distiller 模块

| 文件 | 行数 | 来源 | 职责 |
|------|------|------|------|
| `schemas.py` | 164 | 迁移自 Skill-Distiller-Py | Pydantic 模型：Signal, Skill, DistillResult, AutoGenResult 等 |
| `prompts.py` | 137 | 迁移自 Skill-Distiller-Py | 4 个 LLM System Prompt：FRESH/ACCUMULATE/CLARIFY/AUTO_GEN |
| `engine.py` | 247 | **核心新增** | 蒸馏引擎，通过 LangChain BaseChatModel 调用 LLM，替代裸 httpx |
| `diff.py` | 122 | 迁移自 Skill-Distiller-Py | 规则级 diff + 行级 diff |
| `lint.py` | 79 | 迁移自 Skill-Distiller-Py | SKILL.md 合规校验（三色灯 ok/warn/error） |
| `store.py` | 219 | 迁移自 Skill-Distiller-Py | JSON 持久化，存储路径改为 `~/.langchain_skills/distiller/` |
| `targets.py` | 87 | 迁移自 Skill-Distiller-Py | 导出格式：claude-code / chatgpt / memory |
| `samples.py` | 103 | 迁移自 Skill-Distiller-Py | 3 个示例对话场景：写作/代码审查/设计 |

### stream 模块

| 文件 | 来源 | 职责 |
|------|------|------|
| `emitter.py` | 原样迁移 | StreamEventEmitter，生成 thinking/text/tool_call/tool_result/done/error 事件 |
| `tracker.py` | 原样迁移 | ToolCallTracker，管理流式工具调用的增量 JSON 拼接 |
| `formatter.py` | 原样迁移 | ToolResultFormatter，内容类型检测 + Rich 格式化 |
| `utils.py` | 原样迁移 | 成功/失败前缀常量、路径解析、显示限制 |

### memory 模块

| 文件 | 来源 | 职责 |
|------|------|------|
| `manager.py` | 原样迁移 | MemoryManager 统一门面，关键词自动召回 |
| `session.py` | 原样迁移 | SessionMemory，会话级 volatile 存储 |
| `persistent.py` | 原样迁移 | PersistentMemory，JSON 持久化跨会话存储 |
| `store.py` | 原样迁移 | MemoryStore，底层 JSON 文件 IO |

---

## 关键融合点

### 融合点 1：LLM 调用统一

**问题**：Skill-Distiller-Py 用裸 `httpx` 调 LLM，有独立的 API Key / Base URL / 模型配置。

**方案**：`distiller/engine.py` 通过 Agent 现有的 LangChain `BaseChatModel` 实例调用。

```
旧：engine → httpx.AsyncClient → anthropic/openrouter API
新：engine → BaseChatModel.ainvoke() → 统一 API Key / Base URL / 模型配置
```

- `DistillerEngine.__init__(model: BaseChatModel)` 接收 Agent 已创建的 model 实例
- 提供 `distill()`、`clarify()`、`auto_generate()` 三个同步方法和对应的 `*_stream()` 流式方法
- 输入自动截断至 8000 字符，输出自动提取 JSON（兼容 markdown 代码块包裹）

### 融合点 2：Skill 即时入缓存

**问题**：`SkillLoader` 启动时扫描一次并缓存（`_scanned=True`），蒸馏生成的新 Skill 无法被感知。

**方案**：`skill_loader.py` 新增两个方法：

```python
def invalidate_cache(self):
    """清除扫描缓存，下次 scan_skills() 重新扫描磁盘"""

def register_skill(self, metadata: SkillMetadata):
    """直接注册到缓存，零 IO 开销"""
```

蒸馏工具写完 SKILL.md 后调用 `register_skill()`，新 Skill 立即可被 `load_skill()` 发现。跨 Session 时，磁盘上已有文件，启动扫描自动入库。

### 融合点 3：Agent 自主蒸馏

**问题**：Agent 能用 Skill，但不能创建 Skill。

**方案**：在 `tools.py` 中新增 5 个 `@tool`，通过 `SkillAgentContext.distiller_engine` 访问蒸馏引擎：

| 工具 | 功能 | 产出 |
|------|------|------|
| `distill_skill` | 从对话中蒸馏 Skill | 写入 `skills/` 目录 + 注册缓存 + lint 报告 |
| `auto_create_skill` | 根据需求自动生成 | 写入 `SKILL.md` + `reference.md` + 注册缓存 |
| `lint_skill_content` | 校验 SKILL.md 合规性 | 三色灯检查结果 |
| `diff_skill_versions` | 规则级版本对比 | added / removed / kept |
| `export_skill` | 多格式导出 | claude-code / chatgpt / memory 三种格式 |

`SkillAgentContext` 扩展了一个可选字段：

```python
@dataclass
class SkillAgentContext:
    skill_loader: SkillLoader
    working_directory: Path
    distiller_engine: DistillerEngine | None = None  # 新增
```

Agent 创建时自动初始化：

```python
# agent.py — __init__ 中
if enable_distiller and self._llm_model is not None:
    self.context.distiller_engine = DistillerEngine(
        model=self._llm_model,
        max_tokens=self.max_tokens,
    )
```

### 融合点 4：API 路由合并

原有 Agent 路由和 Distiller 路由合并到同一个 FastAPI 应用中，通过前缀隔离：

```
Agent 路由（不变）：
  GET  /api/health
  GET  /api/config
  GET  /api/skills
  GET  /api/skills/{name}
  WS   /ws/chat

Distiller 路由（新增）：
  GET  /api/distiller/health
  GET  /api/distiller/samples
  GET  /api/distiller/samples/{key}
  POST /api/distiller/distill              （流式蒸馏）
  POST /api/distiller/auto-clarify          （非流式，3 个问题）
  POST /api/distiller/auto-generate         （流式自动生成）
  POST /api/distiller/lint                  （合规校验）
  POST /api/distiller/diff                  （版本对比）
  POST /api/distiller/export                （格式导出）
  GET  /api/distiller/store/skills          （列出已存储 Skill）
  GET  /api/distiller/store/skills/{id}     （查看版本历史）
  DELETE /api/distiller/store/skills/{id}   （删除）
  GET  /api/distiller/targets               （列出导出格式）
```

### 融合点 5：配置统一

| 配置项 | 旧（两个独立项目） | 新（融合后） |
|--------|---------------------|-------------|
| API Key | Skill-Distiller-Py 用 `.env` 独立配置 | 共享 `ANTHROPIC_API_KEY` / `DASHSCOPE_API_KEY` |
| Base URL | Skill-Distiller-Py 用 `OPENROUTER_API_KEY` 判断协议 | 共享 `ANTHROPIC_BASE_URL` |
| 模型 | 各自硬编码 | 共享 `CLAUDE_MODEL` 环境变量 |
| 持久化 | `~/.skill-distiller/store.json` | `~/.langchain_skills/distiller/store.json` |

### 融合点 6：不迁移的文件

| Skill-Distiller-Py 文件 | 不迁移原因 |
|-------------------------|-----------|
| `parse_stream.py` | LangChain 自己处理流式，不需要裸 JSON 解析 |
| `api_server.py` | 路由合并到 langchain_skills 的 api_server.py |
| `web_main.py` | langchain_skills 已有自己的 web_main.py |
| `__init__.py` | 无需 |
| `.env` / `.env.example` | 统一用 langchain_skills 的环境变量 |

---

## 依赖

```
# pyproject.toml
[project.dependencies]
langchain>=1.0.0           # Agent 框架
langchain-anthropic>=1.0.0 # Anthropic Claude
langchain-openai>=1.0.0    # OpenAI 兼容（Qwen / DeepSeek）
langgraph>=1.0.0           # Agent 图执行
pydantic>=2.10.0           # schemas 数据验证（新增）
prompt-toolkit>=3.0.0      # CLI 交互
python-dotenv>=1.0         # .env 加载
pyyaml>=6.0                # YAML frontmatter 解析
rich>=14.2.0               # 终端格式化

[project.optional-dependencies]
web = ["fastapi>=0.115.0", "uvicorn[standard]>=0.34.0"]
dev = ["pytest>=9.0.2"]
```

新增依赖仅 `pydantic>=2.10.0`，其余均为原有依赖。
