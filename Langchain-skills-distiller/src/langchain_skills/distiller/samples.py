"""
示例对话场景
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SampleScenario:
    key: str
    emoji: str
    title: str
    hook: str
    quote: str
    conversation: str
    expected_skill_name: str


WRITING = SampleScenario(
    key="writing",
    emoji="\U0001f4dd",
    title="写作偏好",
    hook="AI 一直用'赋能'和'打造'？",
    quote="I got tired of repeating my writing style on every new chat. — r/OpenAI",
    expected_skill_name="my-writing-voice",
    conversation="""我：帮我写一段公众号开头介绍 SaaS 工具
AI：在如今这个数字化时代，企业需要一款能够全方位赋能业务的 SaaS 工具来打造一站式解决方案，本文将为您深度剖析...
我：太啰嗦了，去掉前两段，不要用"赋能"和"打造"
AI：作为一名 SaaS 行业专家，我将为您持续优化关于工具的全方位介绍...
我：我说了不要套话！要直接、不要 AI 腔！而且也不要 AI 自我介绍
AI：好的。这款工具能帮您...
我：还是不行，我的风格就是：直接进主题、短句、零套话、不要 AI 自我介绍。你能记下来吗？
我：另外补充一下，开头必须是钩子（用具体数字或对比），不是结论
AI：明白了，我记下来了
我：写一段试试
AI：我们用过 12 个 SaaS 工具，最后留下了这 3 个。
我：对，就是这种感觉！""",
)

CODE_REVIEW = SampleScenario(
    key="code-review",
    emoji="\U0001f4bb",
    title="团队代码规范",
    hook="新人入职第一周踩同样的坑？",
    quote="Daily AI users reach 10 PRs in 49 days, vs 91 days without. — DX 2026",
    expected_skill_name="frontend-team-review-rules",
    conversation="""[#frontend-review Slack 群聊节选]

张：这个 component 已经 200 行了，需要拆吗？
李：超过 50 行就要拆，团队规范

王：useState 写了 5 个，太多了吧
李：4 个以上要考虑 useReducer

赵：useEffect 报依赖警告了，怎么处理？
李：别在依赖里随便 push，正确做法是用 useCallback 包起来

钱：API 错误处理我直接 throw 了
李：要用我们的 ApiError class，禁止裸 throw。全局有 ErrorBoundary 接住，单页面不要重复 try-catch

张：还有命名问题
李：组件文件 PascalCase，hook 文件 camelCase，工具文件 kebab-case
李：所有 prop 都要 TypeScript 强类型，不允许 any

我：你能帮我整理一下这些规则成 SKILL.md 吗？让新人入职就能用，Cursor 自动遵守""",
)

DESIGN = SampleScenario(
    key="design",
    emoji="\U0001f3a8",
    title="设计风格",
    hook="design review 决策没沉淀？",
    quote="Decisions in design review evaporate. New designers repeat same mistakes.",
    expected_skill_name="design-system-rules",
    conversation="""[design review 会议节选]

Lead：这个 button padding 给到 24 太大了，我们标准是 16
我：嗯，所有 button 都是 16

Lead：还有 hover state，你给的是变深色——团队规则是发光不变色
我：那是 box-shadow 加 inset 的暗色边？
Lead：对，shadow inset 0 0 0 1px brand-500

Lead：disabled 状态 opacity 不是 0.5，是 0.4
Lead：通用原则是：状态变化优先用发光，其次用变色

Lead：圆角统一 8px，卡片用 12px，模态用 16px
Lead：阴影分三档：sm/md/lg，分别对应 button/card/modal

我：这些规则我整理一下，给团队 SKILL.md 用于 review 检查""",
)

ScenarioKey = str

SAMPLES: dict[str, SampleScenario] = {
    "writing": WRITING,
    "code-review": CODE_REVIEW,
    "design": DESIGN,
}

SCENARIO_ORDER: list[str] = ["writing", "code-review", "design"]
