"""
Pydantic schemas for Skill Distiller.

复刻自 Skill-Distiller-Py 的 distill-schema + auto-gen-schema。
字段顺序 = 五幕/四幕动画触发顺序：
  signals → clusters → skill  (Distill, 五幕)
  intent → outline → skill → reference  (AutoGen, 四幕)
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Signal Types ────────────────────────────────────────────────────

class SignalType(str, Enum):
    preference = "preference"
    constraint = "constraint"
    workflow = "workflow"
    example = "example"


SCENARIO_LABELS: dict[SignalType, dict[str, str]] = {
    SignalType.preference: {"label": "偏好", "emoji": "\U0001f49b", "color": "text-amber-400 bg-amber-500/10 border-amber-500/30"},
    SignalType.constraint: {"label": "约束", "emoji": "\U0001f6ab", "color": "text-rose-400 bg-rose-500/10 border-rose-500/30"},
    SignalType.workflow:   {"label": "工作流", "emoji": "\U0001f504", "color": "text-sky-400 bg-sky-500/10 border-sky-500/30"},
    SignalType.example:    {"label": "示例", "emoji": "\U0001f4cc", "color": "text-violet-400 bg-violet-500/10 border-violet-500/30"},
}


class Signal(BaseModel):
    text: str = Field(description="从对话中提取的原句（不超过 80 字）")
    type: SignalType = Field(description="信号类型")


class Clusters(BaseModel):
    preferences: list[str] = Field(default_factory=list, description="提炼后的偏好列表（已去重 + 概括）")
    constraints: list[str] = Field(default_factory=list, description="提炼后的约束/黑名单列表")
    workflows: list[str] = Field(default_factory=list, description="提炼后的工作流步骤")
    examples: list[str] = Field(default_factory=list, description="具体的对照示例（推荐 ≤ 3 条）")


class Skill(BaseModel):
    name: str = Field(
        default="untitled-skill",
        max_length=64,
        description="skill 标识符 · kebab-case · ≤64 字符",
    )
    description: str = Field(
        default="",
        max_length=1024,
        description="双焦点描述：'这个 skill 做什么 + 何时应该使用'。≤1024 字符 · 单行最佳。",
    )
    body: str = Field(default="", description="Markdown body · 包含必须避免/风格要求/示例对照三段")


class DistillResult(BaseModel):
    """五幕剧场的统一 schema · 一次返回所有字段"""
    signals: list[Signal] = Field(default_factory=list, description="从对话中识别的所有调教信号 · 5-15 条最佳")
    clusters: Clusters = Field(default_factory=Clusters)
    skill: Skill = Field(default_factory=Skill)


# ── Auto-Gen Schemas ────────────────────────────────────────────────

class Intent(BaseModel):
    domain: str = Field(default="general", max_length=60, description="领域 · 简短名词短语")
    primary_task: str = Field(default="", max_length=200, description="核心任务 · 一句话说清这个 skill 主要做什么")
    triggers: list[str] = Field(default_factory=list, description="触发条件 · 何时该激活这个 skill · 2-5 条")
    audience: str = Field(default="AI assistant users", max_length=80, description="使用者画像")


class ExamplePair(BaseModel):
    bad: str = Field(default="", max_length=160, description="反例 · 不该这么做")
    good: str = Field(default="", max_length=160, description="正例 · 应该这么做")
    reason: str = Field(default="", max_length=200, description="为什么这样改")


class Outline(BaseModel):
    rules: list[str] = Field(default_factory=list, description="骨架规则 · 3-10 条祈使句")
    examples: list[ExamplePair] = Field(default_factory=list, description="好/坏对照 · 2-5 组")
    reference_titles: list[str] = Field(default_factory=list, description="配套 reference.md 的 section 标题草案 · 2-5 个")


class ReferenceSection(BaseModel):
    heading: str = Field(default="Section", max_length=60, alias="title", description="二级标题")
    content: str = Field(default="", max_length=800, description="章节正文 · markdown · 每节聚焦一个子主题")

    model_config = {"populate_by_name": True}


class ReferenceDoc(BaseModel):
    title: str = Field(default="Reference", max_length=80, description="reference.md 文档标题")
    sections: list[ReferenceSection] = Field(default_factory=list, description="3-7 节扩展知识")


class AutoGenResult(BaseModel):
    """全自动 Skill 生成 · 四幕 schema"""
    intent: Intent = Field(default_factory=Intent)
    outline: Outline = Field(default_factory=Outline)
    skill: Skill = Field(default_factory=Skill)
    reference: ReferenceDoc = Field(default_factory=ReferenceDoc)


# ── Clarify Schema ──────────────────────────────────────────────────

class ClarifyQuestion(BaseModel):
    q: str = Field(default="", max_length=80, description="澄清问题 · ≤80 字")
    recommended_answer: str = Field(
        default="",
        max_length=120,
        description="推荐答案 · 用户可一键采用 · 必须具体可执行",
    )


class ClarifyResult(BaseModel):
    questions: list[ClarifyQuestion] = Field(
        default_factory=list,
        description="3 个澄清问题，覆盖：使用场景 / 风格偏好 / 必须避免",
    )


# ── Request Schemas ─────────────────────────────────────────────────

class BaseSkillInput(BaseModel):
    name: str = ""
    description: str = ""
    body: str = ""
    version: int = 1


class DistillRequest(BaseModel):
    input: str = ""
    base_skill: BaseSkillInput | None = None


class AutoClarifyRequest(BaseModel):
    input: str = ""


class AutoGenerateRequest(BaseModel):
    input: str = ""
    answers: list[str] | None = Field(default=None)
