---
name: cui-ai-daily
description: 小崔AI每日SKILL新闻概览，为你精选每日最值得关注的AI SKILL技能咨询。触发条件：发送[今日SKILL报告]、生成SKILL日报、获取AI技能资讯。
---

# 小崔AI每日SKILL新闻概览

## 操作步骤

1. **精选资讯抓取** - 使用 tavily-search 搜索近24小时内的AI SKILL技能重要新闻，覆盖权威AI科技媒体（TechCrunch、The Verge、Hacker News等），智能过滤只保留有价值的行业资讯。
2. **智能摘要生成** - 对抓取的内容进行中文精华版提炼，每条资讯生成50-100字的核心要点，并标注关键词标签。
3. **清爽界面展示** - 生成一个包含所有摘要信息的精美HTML页面，顶部显示「小崔AI-SKILL日报-日期」，采用卡片式设计，每条资讯一目了然，每张卡片可直接点击查看原文详情。
4. **一键触发** - 用户发送[今日SKILL报告]指令时，自动执行上述流程，生成并展示HTML报告。

## 脚本执行

**重要：运行脚本时必须使用正确的路径格式！**

- ✅ 正确：`python .claude/skills/cui-ai-daily/scripts/generate_report.py`
- ✅ 正确：`uv run .claude/skills/cui-ai-daily/scripts/generate_report.py`
- ❌ 错误：`uv run D:\workspace\skills-agent-proto-main\.claude\skills\...`（绝对路径）
- ❌ 错误：`./scripts/generate.py`（错误的相对路径）

**必须使用正斜杠 `/`，禁止使用反斜杠 `\`**

## 生成的报告

报告将保存到技能目录：`report.html`