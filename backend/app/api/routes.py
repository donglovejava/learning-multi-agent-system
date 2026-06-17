"""API 路由层（§5.3）。

将 HTTP 请求转换为 ``AgentState``，驱动编排图，再把产出整形为响应模型。
路由只做装配与整形，不含业务逻辑——业务由 Agent / 创新模块承担。

骨架阶段：底层 LLM / 仓储为占位实现，调用真实生成路径会抛 ``NotImplementedError``；
``/health`` 与流程装配可立即验证。接入真实依赖后各端点自动可用。
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.assessment_agent import DIMENSIONS, WARNING_THRESHOLDS, WEIGHTS
from app.agents.base import AgentState
from app.core.config import settings
from app.db.session import get_session
from app.dependencies import get_llm, get_orchestration
from app.schemas.api import (
    AssessmentResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    PathRequest,
    PathResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ResourceRequest,
    ResourceResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """健康检查：探活与环境标识。"""
    return HealthResponse(app=settings.app_name, env=settings.app_env)


@router.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest, graph=Depends(get_orchestration)) -> ChatResponse:
    """对话接口：画像构建与资源请求的统一入口（§5.3）。

    真实数据流：
    1. Orchestrator 识别意图
    2. 若是画像构建意图，走 ProfileAgent.process_reply（LLM 抽取+EWMA+持久化）
    3. 其它意图驱动编排图生成资源
    """
    # 先让 Orchestrator 识别意图
    orchestrator_state: AgentState = {
        "student_id": req.student_id,
        "user_input": req.message,
        "errors": [],
    }
    intent = await get_llm().classify_intent(req.message)

    # 画像构建意图：直接走 ProfileAgent.process_reply，不进入资源生成流程
    if intent == "build_profile":
        from app.dependencies import get_profile_agent
        agent = get_profile_agent()
        result = await agent.process_reply(req.student_id, req.message)
        reply = result.get("question") or result.get("summary") or "好的，我了解了~"
        return ChatResponse(
            reply=reply,
            profile_updated=True,
            explanation=None,
            conversation_id=req.conversation_id or uuid.uuid4().hex,
            profile=result.get("profile"),
            profile_completion=result.get("completion"),
            next_question=result.get("question"),
        )

    # 其它意图：驱动编排图
    orchestrator_state["intent"] = intent
    result = await graph.ainvoke(orchestrator_state)
    return ChatResponse(
        reply=_first_text(result),
        profile_updated=bool(result.get("profile")),
        explanation=result.get("explanation"),
        conversation_id=req.conversation_id or uuid.uuid4().hex,
        profile=result.get("profile"),
    )


@router.post("/api/v1/resources", response_model=ResourceResponse, tags=["resource"])
async def generate_resources(
    req: ResourceRequest, graph=Depends(get_orchestration)
) -> ResourceResponse:
    """资源生成接口：并行生成多种学习资源（§3.1.2，目标 <30s）。"""
    start = time.perf_counter()
    state: AgentState = {
        "student_id": req.student_id,
        "intent": "generate_resource",
        "knowledge_point": req.knowledge_point,
        "resource_types": req.resource_types,
        "scaffold_level": req.scaffold_level or "medium",
        "errors": [],
    }
    result = await graph.ainvoke(state)
    resources = [
        result[key]
        for key in ("document", "quiz", "mindmap", "video", "code", "reading")
        if result.get(key)
    ]
    return ResourceResponse(
        resources=resources,
        generation_time=round(time.perf_counter() - start, 3),
        scaffold_level=result.get("scaffold_level", "medium"),
        explanations=[e for e in [result.get("explanation")] if e],
    )


@router.post("/api/v1/path", response_model=PathResponse, tags=["path"])
async def plan_path(req: PathRequest, graph=Depends(get_orchestration)) -> PathResponse:
    """路径规划接口：DAG + 改进 Dijkstra（§5.3 / §7.4）。"""
    state: AgentState = {
        "student_id": req.student_id,
        "intent": "plan_path",
        "knowledge_point": req.target_knowledge,
        "errors": [],
    }
    result = await graph.ainvoke(state)
    path = result.get("path") or {}
    nodes = path.get("nodes", [])
    # nodes 已是 enriched dict 列表（含 label/difficulty/category），直接透传
    path_nodes = [
        n if isinstance(n, dict) else {"id": n, "label": str(n)}
        for n in nodes
    ]
    return PathResponse(
        path=path_nodes,
        total_nodes=path.get("total_nodes", len(nodes)),
        estimated_weeks=max(1, len(nodes)) * 0.5,
        explanation=result.get("explanation"),
    )


@router.get("/api/v1/profile/{student_id}", response_model=ProfileResponse, tags=["profile"])
async def get_profile(student_id: str, session: AsyncSession = Depends(get_session)) -> ProfileResponse:
    """获取学生画像（§5.3）。接入 PostgreSQL 真实仓储。"""
    from app.db.repository import PostgresRepository

    repo = PostgresRepository(session)
    profile = await repo.get_profile(student_id)
    if not profile:
        # 初始化空画像
        profile = await repo.get_or_create_profile(student_id)
    return ProfileResponse(
        student_id=student_id,
        dimensions=profile,
        radar_data=[
            profile.get("knowledge_base", 0.5),
            profile.get("metacognition", 0.5),
            profile.get("motivation_strength", 0.5),
        ],
        summary=f"学生 {student_id} 的画像",
        version=profile.get("version", 1),
    )


@router.put("/api/v1/profile", response_model=ProfileResponse, tags=["profile"])
async def update_profile(
    req: ProfileUpdateRequest, session: AsyncSession = Depends(get_session)
) -> ProfileResponse:
    """更新画像维度（EWMA，§7.3.1）。接入 PostgreSQL 真实仓储。"""
    from app.db.repository import PostgresRepository

    repo = PostgresRepository(session)
    updated = await repo.update_profile(req.student_id, {req.dimension: req.value})
    return ProfileResponse(
        student_id=req.student_id,
        dimensions=updated,
        radar_data=[
            updated.get("knowledge_base", 0.5),
            updated.get("metacognition", 0.5),
            updated.get("motivation_strength", 0.5),
        ],
        summary=f"学生 {req.student_id} 的画像已更新",
        version=updated.get("version", 1),
    )


@router.get(
    "/api/v1/assessment/{student_id}", response_model=AssessmentResponse, tags=["assessment"]
)
async def get_assessment(
    student_id: str, session: AsyncSession = Depends(get_session)
) -> AssessmentResponse:
    """获取 10 维度学习效果评估（§3.1.4）。接入 PostgreSQL 真实仓储。"""
    from app.db.repository import PostgresRepository

    repo = PostgresRepository(session)
    scores = await repo.compute_assessment_dimensions(student_id, DIMENSIONS)
    total = sum(scores[dim] * w for dim, w in zip(DIMENSIONS, WEIGHTS))
    warnings = [
        {"dimension": dim, "score": scores[dim], "threshold": WARNING_THRESHOLDS[dim]}
        for dim in DIMENSIONS
        if scores[dim] < WARNING_THRESHOLDS[dim]
    ]
    level = "优秀" if total > 0.8 else "良好" if total > 0.6 else "需改进"
    return AssessmentResponse(
        student_id=student_id,
        dimensions=scores,
        total_score=round(total, 4),
        level=level,
        warnings=warnings,
    )


@router.get("/api/v1/knowledge/graph", tags=["knowledge"])
async def get_knowledge_graph() -> dict:
    """返回完整知识图谱（节点 + 前置边），供前端可视化。"""
    from app.dependencies import _get_repo

    repo = _get_repo()
    nodes = repo.all_nodes() if hasattr(repo, "all_nodes") else []
    edges = repo.all_edges() if hasattr(repo, "all_edges") else []
    return {"nodes": nodes, "edges": edges}


@router.get("/api/v1/knowledge/prerequisite/{target}", tags=["knowledge"])
async def get_prerequisite_chain(target: str) -> dict:
    """返回目标知识点的完整前置链（可解释推荐数据源）。"""
    from app.dependencies import _get_repo

    repo = _get_repo()
    chain = repo.prerequisite_chain(target) if hasattr(repo, "prerequisite_chain") else []
    return {"target": target, "chain": chain}


def _first_text(state: AgentState) -> str:
    """从编排结果中提取面向用户的文本回复。

    骨架阶段：优先取 document 内容，否则给出占位提示。
    """
    doc = state.get("document")
    if doc and doc.get("content"):
        return doc["content"]
    return "（骨架占位）已接收请求，接入 LLM 后将返回实际回复。"
