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

from app.agents.base import AgentState
from app.core.config import settings
from app.dependencies import get_orchestration
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

    经 Orchestrator 识别意图后驱动相应流程；此处返回回复与可选解释。
    """
    state: AgentState = {
        "student_id": req.student_id,
        "user_input": req.message,
        "errors": [],
    }
    result = await graph.invoke(state)
    return ChatResponse(
        reply=_first_text(result),
        profile_updated=bool(result.get("profile")),
        explanation=result.get("explanation"),
        conversation_id=req.conversation_id or uuid.uuid4().hex,
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
    result = await graph.invoke(state)
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
    result = await graph.invoke(state)
    path = result.get("path") or {}
    nodes = path.get("nodes", [])
    return PathResponse(
        path=[{"id": n} for n in nodes],
        total_nodes=path.get("total_nodes", len(nodes)),
        estimated_weeks=path.get("estimated_weeks", 0.0),
        explanation=result.get("explanation"),
    )


@router.get("/api/v1/profile/{student_id}", response_model=ProfileResponse, tags=["profile"])
async def get_profile(student_id: str) -> ProfileResponse:
    """获取学生画像（§5.3）。骨架阶段返回空画像结构，待接入仓储。"""
    raise NotImplementedError("get_profile 待接入画像仓储查询")


@router.put("/api/v1/profile", response_model=ProfileResponse, tags=["profile"])
async def update_profile(req: ProfileUpdateRequest) -> ProfileResponse:
    """更新画像维度（EWMA，§7.3.1）。骨架阶段待接入仓储与算法持久化。"""
    raise NotImplementedError("update_profile 待接入画像仓储更新")


@router.get(
    "/api/v1/assessment/{student_id}", response_model=AssessmentResponse, tags=["assessment"]
)
async def get_assessment(student_id: str) -> AssessmentResponse:
    """获取 10 维度学习效果评估（§3.1.4）。骨架阶段待接入行为数据。"""
    raise NotImplementedError("get_assessment 待接入行为数据与 Assessment Agent")


def _first_text(state: AgentState) -> str:
    """从编排结果中提取面向用户的文本回复。

    骨架阶段：优先取 document 内容，否则给出占位提示。
    """
    doc = state.get("document")
    if doc and doc.get("content"):
        return doc["content"]
    return "（骨架占位）已接收请求，接入 LLM 后将返回实际回复。"
