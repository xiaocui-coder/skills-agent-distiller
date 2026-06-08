"""
Skill Distiller — 从对话/需求中自动生成 SKILL.md

核心能力：
- distill: 从对话中提取信号，蒸馏出 SKILL.md
- auto_generate: 根据需求描述自动生成完整 Skill
- lint: 校验 SKILL.md 合规性
- diff: 规则级版本对比
- export: 多格式导出
"""

from .engine import DistillerEngine
from .store import SkillStore
from .schemas import (
    Signal, SignalType, Clusters, Skill,
    DistillResult, AutoGenResult, ClarifyResult,
    DistillRequest, AutoClarifyRequest, AutoGenerateRequest,
)

__all__ = [
    "DistillerEngine",
    "SkillStore",
    "Signal",
    "SignalType",
    "Clusters",
    "Skill",
    "DistillResult",
    "AutoGenResult",
    "ClarifyResult",
    "DistillRequest",
    "AutoClarifyRequest",
    "AutoGenerateRequest",
]
