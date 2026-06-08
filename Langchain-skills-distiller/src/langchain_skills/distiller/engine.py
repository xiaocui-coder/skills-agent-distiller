"""
蒸馏引擎 — 通过 LangChain BaseChatModel 调用 LLM

替代 Skill-Distiller-Py 的裸 httpx 调用，统一 API Key / Base URL / 模型配置。
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .schemas import (
    AutoGenResult,
    ClarifyResult,
    DistillResult,
)
from .prompts import SYSTEM_ACCUMULATE, SYSTEM_AUTO_GEN, SYSTEM_CLARIFY, SYSTEM_FRESH

logger = logging.getLogger(__name__)

if os.getenv("SKILLS_DEBUG", "").lower() in frozenset({"1", "true", "yes"}):
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[DISTILLER] %(message)s"))
    logger.addHandler(handler)

_MAX_INPUT_LEN = 8000

_CAMEL_SNAKE_RE = re.compile(r'([a-z0-9])([A-Z])')


def _camel_to_snake_keys(data: dict) -> dict:
    """递归地将 dict 中所有 camelCase 键转为 snake_case"""
    result = {}
    for key, value in data.items():
        snake_key = _CAMEL_SNAKE_RE.sub(r'\1_\2', key).lower()
        if isinstance(value, dict):
            value = _camel_to_snake_keys(value)
        elif isinstance(value, list):
            value = [_camel_to_snake_keys(item) if isinstance(item, dict) else item for item in value]
        result[snake_key] = value
    return result


def _truncate(text: str, max_len: int = _MAX_INPUT_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n[输入已截断，原文 {len(text)} 字符，仅保留前 {max_len} 字符]"


def _fix_json_control_chars(text: str) -> str:
    """修复 JSON 字符串值中的非法控制字符（裸换行、tab 等）。

    LLM 经常在 JSON 的字符串值内输出未转义的换行符，导致 json.loads 失败。
    此函数仅在字符串内部（引号之间）修复这些字符，不影响 JSON 结构。
    """
    result = []
    in_str = False
    escaped = False
    for ch in text:
        if escaped:
            result.append(ch)
            escaped = False
            continue
        if ch == '\\' and in_str:
            result.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_str = not in_str
            result.append(ch)
            continue
        if in_str and ch in '\n\r\t':
            if ch == '\n':
                result.append('\\n')
            elif ch == '\r':
                result.append('\\r')
            elif ch == '\t':
                result.append('\\t')
            continue
        result.append(ch)
    return ''.join(result)


def _find_json_bounds(text: str) -> int:
    """找到第一个完整 JSON 对象的结束位置，返回结束索引（不含 }）。"""
    depth = 0
    start = -1
    in_str = False
    escaped = False
    for i, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == '\\' and in_str:
            escaped = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                return i + 1
    return -1


def _extract_json(text: str) -> dict | None:
    """从 LLM 回复中提取 JSON，兼容 markdown 代码块包裹和字符串内裸换行。"""
    # 去掉 markdown 代码块
    text = re.sub(r"^```(?:json)?\s*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # 找到 JSON 对象边界
    end = _find_json_bounds(text)
    if end < 0:
        return None

    json_str = text[:end]
    json_str = _fix_json_control_chars(json_str)

    try:
        result = json.loads(json_str)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    return None


def _parse_model(raw: str, model_class, field_name: str = "result"):
    """通用解析：先提取 JSON 再宽松验证，失败时尝试从部分数据构建"""
    data = _extract_json(raw)

    logger.debug(f"[{field_name}] _extract_json returned: {type(data)}")
    if data:
        logger.debug(f"[{field_name}] JSON keys: {list(data.keys())}")

    # camelCase → snake_case（LLM 经常输出 camelCase）
    if isinstance(data, dict):
        data = _camel_to_snake_keys(data)

    # 尝试用转换后的 dict 解析
    if data:
        try:
            return model_class.model_validate(data)
        except Exception as e:
            logger.debug(f"{field_name} model_validate failed: {e}")
        try:
            return model_class.model_validate(data, strict=False)
        except Exception as e:
            logger.debug(f"{field_name} strict=False failed: {e}")

    # 尝试从原始文本直接解析
    try:
        return model_class.model_validate_json(raw)
    except Exception:
        pass

    # 最后兜底：构造空对象
    logger.warning(f"Failed to parse {field_name}, returning empty object. Raw length: {len(raw)}")
    logger.warning(f"[{field_name}] Raw (first 500 chars): {raw[:500]}")
    return model_class()


def _parse_distill_result(raw: str) -> DistillResult:
    """解析蒸馏结果"""
    return _parse_model(raw, DistillResult, "DistillResult")


def _parse_clarify_result(raw: str) -> ClarifyResult:
    """解析澄清问题结果"""
    return _parse_model(raw, ClarifyResult, "ClarifyResult")


def _parse_auto_gen_result(raw: str) -> AutoGenResult:
    """解析自动生成结果"""
    return _parse_model(raw, AutoGenResult, "AutoGenResult")


class DistillerEngine:
    """
    蒸馏引擎 — 封装 LLM 调用逻辑，复用 LangChain ChatModel。

    通过 Agent 现有的 BaseChatModel 实例调用，统一 API Key / Base URL 配置。
    """

    def __init__(self, model: BaseChatModel, max_tokens: int = 16384):
        self.model = model
        self.max_tokens = max_tokens
        # 蒸馏用低温度，提高 JSON 输出稳定性
        try:
            self._model = model.bind(temperature=0.3)
        except Exception:
            self._model = model

    async def distill(
        self,
        input_text: str,
        base_skill: dict | None = None,
    ) -> DistillResult:
        """从对话中蒸馏出 SKILL.md"""
        input_text = _truncate(input_text)

        if base_skill:
            version = base_skill.get("version", 1)
            system = SYSTEM_ACCUMULATE.format(N=version, N_plus_1=version + 1)
            skill_body = base_skill.get("body", "")
            user_content = (
                f"现有 Skill (v{version}):\n"
                f"```\n"
                f"name: {base_skill.get('name', '')}\n"
                f"description: {base_skill.get('description', '')}\n"
                f"\n{skill_body}\n"
                f"```\n\n"
                f"新对话:\n{input_text}"
            )
        else:
            system = SYSTEM_FRESH
            user_content = input_text

        response = await self._model.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=user_content),
        ])
        raw = response.content if isinstance(response.content, str) else str(response.content)
        return _parse_distill_result(raw)

    async def clarify(self, input_text: str) -> ClarifyResult:
        """根据需求生成 3 个澄清问题"""
        input_text = _truncate(input_text)

        response = await self._model.ainvoke([
            SystemMessage(content=SYSTEM_CLARIFY),
            HumanMessage(content=input_text),
        ])
        raw = response.content if isinstance(response.content, str) else str(response.content)
        return _parse_clarify_result(raw)

    async def auto_generate(
        self,
        input_text: str,
        answers: list[str] | None = None,
    ) -> AutoGenResult:
        """根据需求描述自动生成完整 Skill"""
        input_text = _truncate(input_text)

        user_content = input_text
        if answers:
            user_content += "\n\n用户的回答:\n" + "\n".join(f"- {a}" for a in answers)

        response = await self._model.ainvoke([
            SystemMessage(content=SYSTEM_AUTO_GEN),
            HumanMessage(content=user_content),
        ])
        raw = response.content if isinstance(response.content, str) else str(response.content)
        return _parse_auto_gen_result(raw)

    async def distill_stream(
        self,
        input_text: str,
        base_skill: dict | None = None,
    ) -> AsyncIterator[dict]:
        """流式蒸馏 — 逐 chunk yield 中间状态"""
        input_text = _truncate(input_text)

        if base_skill:
            version = base_skill.get("version", 1)
            system = SYSTEM_ACCUMULATE.format(N=version, N_plus_1=version + 1)
            skill_body = base_skill.get("body", "")
            user_content = (
                f"现有 Skill (v{version}):\n"
                f"```\n"
                f"name: {base_skill.get('name', '')}\n"
                f"description: {base_skill.get('description', '')}\n"
                f"\n{skill_body}\n"
                f"```\n\n"
                f"新对话:\n{input_text}"
            )
        else:
            system = SYSTEM_FRESH
            user_content = input_text

        accumulated = ""
        async for chunk in self._model.astream([
            SystemMessage(content=system),
            HumanMessage(content=user_content),
        ]):
            token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            accumulated += token
            yield {"type": "chunk", "content": token}

        # 最终解析
        try:
            result = _parse_distill_result(accumulated)
            yield {"type": "done", "result": result.model_dump()}
        except Exception as e:
            yield {"type": "error", "message": f"解析蒸馏结果失败: {e}", "raw": accumulated}

    async def auto_generate_stream(
        self,
        input_text: str,
        answers: list[str] | None = None,
    ) -> AsyncIterator[dict]:
        """流式自动生成 — 逐 chunk yield 中间状态"""
        input_text = _truncate(input_text)

        user_content = input_text
        if answers:
            user_content += "\n\n用户的回答:\n" + "\n".join(f"- {a}" for a in answers)

        accumulated = ""
        async for chunk in self._model.astream([
            SystemMessage(content=SYSTEM_AUTO_GEN),
            HumanMessage(content=user_content),
        ]):
            token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            accumulated += token
            yield {"type": "chunk", "content": token}

        try:
            result = _parse_auto_gen_result(accumulated)
            yield {"type": "done", "result": result.model_dump()}
        except Exception as e:
            yield {"type": "error", "message": f"解析生成结果失败: {e}", "raw": accumulated}
