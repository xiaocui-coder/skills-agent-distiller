"""FastAPI + WebSocket backend for LangChain Skills Agent with Distiller fusion."""

import asyncio
import os
import re
from collections.abc import AsyncGenerator
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from .agent import LangChainSkillsAgent, check_api_credentials
from .skill_loader import SkillLoader

_agent: LangChainSkillsAgent | None = None
_skill_loader: SkillLoader | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent, _skill_loader
    _skill_loader = SkillLoader()
    if check_api_credentials():
        _agent = LangChainSkillsAgent()
    yield
    _agent = None
    _skill_loader = None


app = FastAPI(title="Skills Agent + Distiller", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
# Agent 路由（原有）
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    distiller_ready = _agent is not None and _agent.context.distiller_engine is not None
    return {"status": "ok", "agent_ready": _agent is not None, "distiller_ready": distiller_ready}


@app.get("/api/config")
async def config():
    return {
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
        "thinking_enabled": True,
        "distiller_enabled": True,
    }


@app.get("/api/skills")
async def list_skills():
    if not _skill_loader:
        return []
    skills = _skill_loader.scan_skills()
    return [
        {
            "name": s.name,
            "description": s.description,
            "path": str(s.skill_path),
        }
        for s in skills
    ]


@app.get("/api/skills/{name}")
async def get_skill(name: str):
    if not _skill_loader:
        return {"error": "Skill loader not initialized"}, 404
    content = _skill_loader.load_skill(name)
    if not content:
        return {"error": f"Skill '{name}' not found"}, 404
    return {
        "name": content.metadata.name,
        "description": content.metadata.description,
        "instructions": content.instructions,
    }


class _StopIteration(Exception):
    pass


async def _stream_in_thread(gen) -> AsyncGenerator[dict, None]:
    loop = asyncio.get_event_loop()

    def _next():
        try:
            return next(gen)
        except StopIteration:
            raise _StopIteration

    while True:
        try:
            event = await loop.run_in_executor(None, _next)
            yield event
        except _StopIteration:
            break
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            break


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") != "message":
                continue
            message = data["content"]
            thread_id = data.get("thread_id", "default")

            if not _agent:
                await websocket.send_json({
                    "type": "error",
                    "message": "Agent not initialized. Check API credentials.",
                })
                continue

            await websocket.send_json({"type": "stream_start", "thread_id": thread_id})

            async for event in _stream_in_thread(_agent.stream_events(message, thread_id)):
                await websocket.send_json(event)

    except WebSocketDisconnect:
        pass


# ═══════════════════════════════════════════════════════════════════
# Distiller 路由（新增）
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/distiller/health")
async def distiller_health():
    engine = _agent.context.distiller_engine if _agent else None
    return {
        "status": "ok" if engine else "unavailable",
        "agent_ready": _agent is not None,
        "distiller_ready": engine is not None,
    }


@app.get("/api/distiller/samples")
async def list_samples():
    """列出可用的示例对话场景"""
    from .distiller.samples import SAMPLES
    return [
        {
            "key": s.key,
            "title": s.title,
            "emoji": s.emoji,
            "hook": s.hook,
            "expected_skill_name": s.expected_skill_name,
            "conversation_length": len(s.conversation),
        }
        for s in SAMPLES.values()
    ]


@app.get("/api/distiller/samples/{key}")
async def get_sample(key: str):
    """获取指定示例对话的完整内容"""
    from .distiller.samples import SAMPLES
    scenario = SAMPLES.get(key)
    if not scenario:
        return {"error": f"Sample '{key}' not found"}, 404
    return {
        "key": scenario.key,
        "title": scenario.title,
        "emoji": scenario.emoji,
        "hook": scenario.hook,
        "quote": scenario.quote,
        "conversation": scenario.conversation,
        "expected_skill_name": scenario.expected_skill_name,
    }


@app.post("/api/distiller/distill")
async def post_distill(req: dict):
    """流式蒸馏：从对话中生成/升级 Skill"""
    from .distiller.schemas import DistillRequest
    from fastapi.responses import StreamingResponse

    if not _agent or not _agent.context.distiller_engine:
        return {"error": "Distiller engine not initialized"}, 503

    try:
        parsed = DistillRequest(**req)
    except Exception as e:
        return {"error": f"Invalid request: {e}"}, 400

    engine = _agent.context.distiller_engine

    base_skill = None
    if parsed.base_skill:
        base_skill = parsed.base_skill.model_dump()

    async def generate():
        async for chunk in engine.distill_stream(parsed.input, base_skill):
            import json
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/distiller/auto-clarify")
async def post_auto_clarify(req: dict):
    """生成 3 个澄清问题（非流式）"""
    from .distiller.schemas import AutoClarifyRequest

    if not _agent or not _agent.context.distiller_engine:
        return {"error": "Distiller engine not initialized"}, 503

    try:
        parsed = AutoClarifyRequest(**req)
    except Exception as e:
        return {"error": f"Invalid request: {e}"}, 400

    result = await _agent.context.distiller_engine.clarify(parsed.input)
    return result.model_dump()


@app.post("/api/distiller/auto-generate")
async def post_auto_generate(req: dict):
    """流式自动生成完整 Skill"""
    from .distiller.schemas import AutoGenerateRequest
    from fastapi.responses import StreamingResponse

    if not _agent or not _agent.context.distiller_engine:
        return {"error": "Distiller engine not initialized"}, 503

    try:
        parsed = AutoGenerateRequest(**req)
    except Exception as e:
        return {"error": f"Invalid request: {e}"}, 400

    engine = _agent.context.distiller_engine

    async def generate():
        async for chunk in engine.auto_generate_stream(parsed.input, parsed.answers):
            import json
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/distiller/lint")
async def post_lint(req: dict):
    """校验 SKILL.md 内容"""
    from .distiller.schemas import Skill
    from .distiller.lint import lint_skill as do_lint

    body = req.get("body", "")
    skill = Skill(
        name=req.get("name", "temp"),
        description=req.get("description", ""),
        body=body,
    )
    items = do_lint(skill)
    return {
        "items": [
            {"field": i.field, "level": i.level, "message": i.message, "rule": i.rule}
            for i in items
        ],
        "summary": {
            field: next(
                (i.level for i in items if i.field == field),
                "ok",
            )
            for field in ["name", "description", "body"]
        },
    }


@app.post("/api/distiller/diff")
async def post_diff(req: dict):
    """规则级 diff 对比"""
    from .distiller.diff import diff_rules

    old_body = req.get("old_body", "")
    new_body = req.get("new_body", "")
    result = diff_rules(old_body, new_body)
    return {
        "added": [
            {"section": r.section, "text": r.text, "raw": r.raw}
            for r in result.added
        ],
        "removed": [
            {"section": r.section, "text": r.text, "raw": r.raw}
            for r in result.removed
        ],
        "kept": [
            {"section": r.section, "text": r.text, "raw": r.raw}
            for r in result.kept
        ],
        "stats": {
            "added": len(result.added),
            "removed": len(result.removed),
            "kept": len(result.kept),
        },
    }


@app.post("/api/distiller/export")
async def post_export(req: dict):
    """导出 Skill 为不同格式"""
    from .distiller.schemas import Skill
    from .distiller.targets import TARGETS, to_claude_code_md, to_chatgpt_instructions, to_memory_short

    skill_name = req.get("skill_name", "")
    target = req.get("target", "claude-code")

    if not _skill_loader:
        return {"error": "Skill loader not initialized"}, 503

    content = _skill_loader.load_skill(skill_name)
    if not content:
        return {"error": f"Skill '{skill_name}' not found"}, 404

    skill = Skill(
        name=content.metadata.name,
        description=content.metadata.description,
        body=content.instructions,
    )

    export_map = {
        "claude-code": to_claude_code_md,
        "chatgpt": to_chatgpt_instructions,
        "memory": to_memory_short,
    }

    if target not in export_map:
        return {"error": f"Unknown target '{target}'. Available: {list(export_map.keys())}"}, 400

    target_info = next((t for t in TARGETS if t.key == target), None)
    return {
        "target": target,
        "filename": target_info.filename if target_info else f"{skill_name}.{target}",
        "content": export_map[target](skill),
        "hint": target_info.hint if target_info else "",
    }


@app.get("/api/distiller/store/skills")
async def list_stored_skills():
    """列出 Distiller 持久化存储中的所有 Skill（含版本历史）"""
    from .distiller.store import SkillStore

    store = SkillStore()
    return [
        {
            "id": s.id,
            "name": s.name,
            "scenario": s.scenario,
            "source": s.source,
            "versions_count": len(s.versions),
            "latest_version": s.versions[-1].v if s.versions else 0,
            "created_at": s.created_at,
        }
        for s in store.library
    ]


@app.get("/api/distiller/store/skills/{skill_id}")
async def get_stored_skill(skill_id: str):
    """查看 Skill 详细版本历史"""
    from .distiller.store import SkillStore

    store = SkillStore()
    skill = store.get_skill(skill_id)
    if not skill:
        return {"error": "Skill not found"}, 404
    return {
        "id": skill.id,
        "name": skill.name,
        "scenario": skill.scenario,
        "source": skill.source,
        "versions": [
            {
                "v": v.v,
                "description": v.description,
                "body": v.body,
                "signal_count": v.signal_count,
                "added_conversation": v.added_conversation,
                "created_at": v.created_at,
            }
            for v in skill.versions
        ],
        "created_at": skill.created_at,
    }


@app.delete("/api/distiller/store/skills/{skill_id}")
async def delete_stored_skill(skill_id: str):
    """删除存储的 Skill"""
    from .distiller.store import SkillStore

    store = SkillStore()
    skill = store.get_skill(skill_id)
    if not skill:
        return {"error": "Skill not found"}, 404
    store.remove_skill(skill_id)
    return {"status": "ok", "deleted": skill_id}


@app.get("/api/distiller/targets")
async def list_export_targets():
    """列出所有可用的导出格式"""
    from .distiller.targets import TARGETS
    return [
        {
            "key": t.key,
            "title": t.title,
            "emoji": t.emoji,
            "filename": t.filename,
            "description": t.description,
            "hint": t.hint,
        }
        for t in TARGETS
    ]


# ── Save Skill to Disk ────────────────────────────────────────────────

class SaveSkillRequest(BaseModel):
    name: str
    description: str = ""
    body: str = ""
    reference_title: str = ""
    reference_sections: list[dict] = []


@app.post("/api/distiller/save-skill")
async def save_skill_to_disk(req: SaveSkillRequest):
    """将蒸馏/自动生成的 Skill 保存到 .claude/skills/{name}/ 目录。"""
    from .distiller.targets import to_claude_code_md
    from .distiller.schemas import Skill

    if not req.name or not req.body:
        return {"status": "error", "message": "name 和 body 不能为空"}

    skill_dir = Path.cwd() / ".claude" / "skills" / req.name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill = Skill(name=req.name, description=req.description, body=req.body)
    skill_md = to_claude_code_md(skill)
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    saved_files = [f".claude/skills/{req.name}/SKILL.md"]

    # 保存 reference 到 references/ 子目录
    if req.reference_sections:
        ref_dir = skill_dir / "references"
        ref_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9一-鿿\-]', '_', req.name)
        ref_filename = f"{safe_name}-reference.md"
        ref_lines = [f"# {req.reference_title or req.name + ' Reference'}", ""]
        for sec in req.reference_sections:
            ref_lines.append(f"## {sec.get('title', 'Section')}")
            ref_lines.append("")
            ref_lines.append(sec.get("content", ""))
            ref_lines.append("")
        (ref_dir / ref_filename).write_text("\n".join(ref_lines), encoding="utf-8")
        saved_files.append(f".claude/skills/{req.name}/references/{ref_filename}")

    # 注册到 SkillLoader 缓存
    if _skill_loader:
        from .skill_loader import SkillMetadata
        _skill_loader.register_skill(SkillMetadata(
            name=req.name,
            description=req.description,
            skill_path=skill_dir,
        ))
        _skill_loader.invalidate_cache()

    return {"status": "ok", "saved_files": saved_files, "skill_dir": str(skill_dir)}
