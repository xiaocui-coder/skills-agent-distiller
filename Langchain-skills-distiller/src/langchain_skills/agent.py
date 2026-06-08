"""
LangChain Skills Agent 主体（含 Distiller 融合版）

使用 LangChain 1.0 的 create_agent API 实现 Skills Agent，演示三层加载机制：
- Level 1: 启动时将 Skills 元数据注入 system_prompt
- Level 2: load_skill tool 加载详细指令
- Level 3: bash tool 执行脚本

扩展能力：
- DistillerEngine: 蒸馏/自动生成 SKILL.md
- SkillLoader.register_skill(): 新 Skill 即时入缓存
"""

import os
from pathlib import Path
from typing import Optional, Iterator

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver

from .skill_loader import SkillLoader
from .tools import ALL_TOOLS, SkillAgentContext
from .stream import StreamEventEmitter, ToolCallTracker, is_success, DisplayLimits

load_dotenv(override=True)

DEFAULT_MODEL = os.getenv("CLAUDE_MODEL")
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "0")) or None
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0")) or None
DEFAULT_THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "0")) or None

QWEN_MODEL_PREFIXES = tuple(
    p.strip()
    for p in os.getenv("QWEN_MODEL_PREFIXES", "").split(",")
    if p.strip()
)
QWEN_DEFAULT_MODEL = os.getenv("QWEN_DEFAULT_MODEL")
QWEN_DASHSCOPE_BASE_URL = os.getenv("QWEN_BASE_URL")

_BASE_PROMPT = (
    "You are a helpful coding assistant with access to specialized skills.\n\n"
    "Your capabilities include:\n"
    "- Loading and using specialized skills for specific tasks\n"
    "- Executing bash commands and scripts\n"
    "- Reading and writing files\n"
    "- Following skill instructions to complete complex tasks\n\n"
    "When a user request matches a skill's description, "
    "use the load_skill tool to get detailed instructions before proceeding.\n\n"
    "## Distiller Capabilities\n"
    "You can also create new skills:\n"
    "- `distill_skill`: Extract skills from conversations\n"
    "- `auto_create_skill`: Generate skills from requirement descriptions\n"
    "- `lint_skill_content`: Validate skill compliance\n"
    "- `diff_skill_versions`: Compare skill versions\n"
    "- `export_skill`: Export skills to different formats\n\n"
    "## Knowledge Base Default Path\n"
    "The knowledge base is located at `knowledge/` directory in the current project root. "
    "When using kb-retriever skill, use `knowledge/` as the default path."
)

_DEBUG_FLAGS = frozenset({"1", "true", "yes"})


def get_anthropic_credentials() -> tuple[Optional[str], Optional[str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    return api_key, base_url


def get_qwen_credentials() -> tuple[Optional[str], Optional[str]]:
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    base_url = os.getenv("QWEN_BASE_URL")
    return api_key, base_url


def check_api_credentials() -> bool:
    return bool(get_anthropic_credentials()[0] or get_qwen_credentials()[0])


def is_qwen_model(model_name: str) -> bool:
    prefix = model_name.lower()
    return any(prefix.startswith(p) for p in QWEN_MODEL_PREFIXES)


def _extract_args(args) -> dict:
    """确保 args 是 dict 类型"""
    return args if isinstance(args, dict) else {}


class LangChainSkillsAgent:
    """基于 LangChain 1.0 的 Skills Agent（含 Distiller 融合）"""

    def __init__(
        self,
        model: Optional[str] = None,
        skill_paths: Optional[list[Path]] = None,
        working_directory: Optional[Path] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        enable_thinking: bool = True,
        thinking_budget: Optional[int] = None,
        enable_distiller: bool = True,
    ):
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget or DEFAULT_THINKING_BUDGET
        self.model_name = model or DEFAULT_MODEL or ""
        self.max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        self.temperature = 1.0 if enable_thinking else (
            temperature or DEFAULT_TEMPERATURE
        )
        self.working_directory = working_directory or Path.cwd()
        self.enable_distiller = enable_distiller

        self.skill_loader = SkillLoader(skill_paths)
        self.system_prompt = self.skill_loader.build_system_prompt(_BASE_PROMPT)
        self.context = SkillAgentContext(
            skill_loader=self.skill_loader,
            working_directory=self.working_directory,
        )

        self._llm_model: BaseChatModel | None = None
        self.agent = self._create_agent()

        # 初始化 DistillerEngine
        if enable_distiller and self._llm_model is not None:
            from .distiller.engine import DistillerEngine
            self.context.distiller_engine = DistillerEngine(
                model=self._llm_model,
                max_tokens=self.max_tokens,
            )

    def _create_agent(self):
        if is_qwen_model(self.model_name):
            return self._create_qwen_agent()
        return self._create_anthropic_agent()

    def _create_qwen_agent(self):
        from langchain_openai import ChatOpenAI

        api_key, base_url = get_qwen_credentials()
        if not api_key:
            raise ValueError(
                "请配置通义千问 API Key: 设置 DASHSCOPE_API_KEY 或 QWEN_API_KEY 环境变量"
            )
        model = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=api_key,
            base_url=base_url or QWEN_DASHSCOPE_BASE_URL,
            streaming=True,
        )
        self._llm_model = model
        return create_agent(
            model=model, tools=ALL_TOOLS,
            system_prompt=self.system_prompt,
            context_schema=SkillAgentContext,
            checkpointer=InMemorySaver(),
        )

    def _create_anthropic_agent(self):
        from langchain_anthropic import ChatAnthropic

        api_key, base_url = get_anthropic_credentials()
        if not api_key:
            raise ValueError(
                "请配置 Anthropic API Key: 设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN 环境变量"
            )
        init_kwargs: dict = {
            "model": self.model_name,
            "temperature": 1.0 if self.enable_thinking else self.temperature,
            "max_tokens": self.max_tokens,
            "api_key": api_key,
        }
        if base_url:
            init_kwargs["base_url"] = base_url

        model = ChatAnthropic(**init_kwargs)
        self._llm_model = model
        return create_agent(
            model=model, tools=ALL_TOOLS,
            system_prompt=self.system_prompt,
            context_schema=SkillAgentContext,
            checkpointer=InMemorySaver(),
        )

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def get_discovered_skills(self) -> list[dict]:
        return [
            {"name": s.name, "description": s.description, "path": str(s.skill_path)}
            for s in self.skill_loader.scan_skills()
        ]

    def invoke(self, message: str, thread_id: str = "default") -> dict:
        config = {"configurable": {"thread_id": thread_id}}
        return self.agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            context=self.context,
        )

    def stream(self, message: str, thread_id: str = "default") -> Iterator[dict]:
        config = {"configurable": {"thread_id": thread_id}}
        for chunk in self.agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            context=self.context,
            stream_mode="values",
        ):
            yield chunk

    def stream_events(self, message: str, thread_id: str = "default") -> Iterator[dict]:
        config = {"configurable": {"thread_id": thread_id}}
        emitter = StreamEventEmitter()
        tracker = ToolCallTracker()
        full_response = ""
        debug = os.getenv("SKILLS_DEBUG", "").lower() in _DEBUG_FLAGS

        try:
            for event in self.agent.stream(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
                context=self.context,
                stream_mode="messages",
            ):
                chunk = event[0] if isinstance(event, tuple) and len(event) >= 2 else event

                if debug:
                    print(f"[DEBUG] Event: {type(chunk).__name__}")

                if isinstance(chunk, (AIMessageChunk, AIMessage)):
                    for ev in self._process_chunk_content(chunk, emitter, tracker):
                        if ev.type == "text":
                            full_response += ev.data.get("content", "")
                        if debug:
                            print(f"[DEBUG] Yielding: {ev.type}")
                        yield ev.data

                    if getattr(chunk, "tool_calls", None):
                        for ev in self._process_tool_calls(chunk.tool_calls, emitter, tracker):
                            if debug:
                                print(f"[DEBUG] Yielding from tool_calls: {ev.type}")
                            yield ev.data

                elif getattr(chunk, "type", None) == "tool":
                    if debug:
                        print(f"[DEBUG] Processing tool result: {getattr(chunk, 'name', 'unknown')}")
                    for ev in self._process_tool_result(chunk, emitter, tracker):
                        if debug:
                            print(f"[DEBUG] Yielding: {ev.type}")
                        yield ev.data

        except Exception as e:
            if debug:
                import traceback
                print(f"[DEBUG] Stream error: {e}")
                traceback.print_exc()
            yield emitter.error(str(e)).data

        yield emitter.done(full_response).data

    def _process_chunk_content(self, chunk, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        content = chunk.content

        if isinstance(content, str):
            if content:
                yield emitter.text(content)
            return

        blocks = getattr(chunk, "content_blocks", None)
        if blocks is None:
            blocks = [content] if isinstance(content, dict) else (
                content if isinstance(content, list) else None
            )
        if blocks is None:
            return

        for raw_block in blocks:
            if not isinstance(raw_block, dict):
                try:
                    raw_block = raw_block.model_dump()
                except Exception:
                    continue

            block_type = raw_block.get("type")

            if block_type in ("thinking", "reasoning"):
                text = raw_block.get("thinking") or raw_block.get("reasoning") or ""
                if text:
                    yield emitter.thinking(text)

            elif block_type == "text":
                text = raw_block.get("text") or raw_block.get("content") or ""
                if text:
                    yield emitter.text(text)

            elif block_type in ("tool_use", "tool_call"):
                self._handle_tool_block(raw_block, emitter, tracker)

            elif block_type == "input_json_delta":
                partial = raw_block.get("partial_json", "")
                if partial:
                    tracker.append_json_delta(partial, raw_block.get("index", 0))

            elif block_type == "tool_call_chunk":
                tool_id = raw_block.get("id", "")
                if tool_id:
                    tracker.update(tool_id, name=raw_block.get("name", ""))
                partial_args = raw_block.get("args", "")
                if isinstance(partial_args, str) and partial_args:
                    tracker.append_json_delta(partial_args, raw_block.get("index", 0))

    def _handle_tool_block(self, block: dict, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        tool_id = block.get("id", "")
        if not tool_id:
            return
        name = block.get("name", "")
        args = _extract_args(block.get("input") if block.get("type") == "tool_use" else block.get("args"))
        tracker.update(tool_id, name=name, args=args)
        if tracker.is_ready(tool_id):
            tracker.mark_emitted(tool_id)
            yield emitter.tool_call(name, args, tool_id)

    def _process_tool_calls(self, tool_calls: list, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        for tc in tool_calls:
            tool_id = tc.get("id", "")
            if not tool_id:
                continue
            name = tc.get("name", "")
            args = _extract_args(tc.get("args"))
            tracker.update(tool_id, name=name, args=args)
            if tracker.is_ready(tool_id):
                tracker.mark_emitted(tool_id)
                yield emitter.tool_call(name, args, tool_id)

    def _process_tool_result(self, chunk, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        tracker.finalize_all()

        for info in tracker.get_pending():
            info.emitted = True
            yield emitter.tool_call(info.name, info.args, info.id)

        name = getattr(chunk, "name", "unknown")
        raw_content = str(getattr(chunk, "content", ""))
        content = raw_content[:DisplayLimits.TOOL_RESULT_MAX]
        if len(raw_content) > DisplayLimits.TOOL_RESULT_MAX:
            content += "\n... (truncated)"

        yield emitter.tool_result(name, content, is_success(content))

    def get_last_response(self, result: dict) -> str:
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                if isinstance(msg.content, str):
                    return msg.content
                if isinstance(msg.content, list):
                    text_parts = [
                        part.get("text", "")
                        for part in msg.content
                        if isinstance(part, dict) and part.get("type") == "text"
                    ]
                    if text_parts:
                        return "\n".join(text_parts)
        return ""


def create_skills_agent(
    model: Optional[str] = None,
    skill_paths: Optional[list[Path]] = None,
    working_directory: Optional[Path] = None,
    enable_thinking: bool = True,
    thinking_budget: Optional[int] = None,
    enable_distiller: bool = True,
) -> LangChainSkillsAgent:
    return LangChainSkillsAgent(
        model=model,
        skill_paths=skill_paths,
        working_directory=working_directory,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
        enable_distiller=enable_distiller,
    )
