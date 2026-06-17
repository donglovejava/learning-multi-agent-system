"""API 请求/响应模型（§5.3）。

对齐设计文档接口契约：对话、资源生成、路径规划、画像、评估。
``any`` 在原文档中为占位，此处用具体类型收敛以获得校验与文档生成能力。
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

# === 通用 ===


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    env: str


# === 对话（画像构建 + 资源请求入口）===


class ChatRequest(BaseModel):
    student_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    profile_updated: bool = False
    explanation: Optional[str] = None
    conversation_id: str
    profile: Optional[dict[str, Any]] = None
    profile_completion: Optional[float] = None
    next_question: Optional[str] = None


# === 资源生成 ===

#: 合法资源类型（§3.1.2 六种资源）
RESOURCE_TYPES = ["document", "quiz", "mindmap", "video", "code", "reading"]


class ResourceRequest(BaseModel):
    student_id: str
    knowledge_point: str
    resource_types: list[str] = Field(default_factory=lambda: ["document", "quiz", "mindmap"])
    scaffold_level: Optional[str] = None


class ResourceResponse(BaseModel):
    resources: list[dict[str, Any]]
    generation_time: float
    scaffold_level: str
    explanations: list[str] = Field(default_factory=list)


# === 路径规划 ===


class PathRequest(BaseModel):
    student_id: str
    target_knowledge: str


class PathResponse(BaseModel):
    path: list[dict[str, Any]]
    total_nodes: int
    estimated_weeks: float = 0.0
    explanation: Optional[str] = None


# === 画像 ===


class ProfileUpdateRequest(BaseModel):
    student_id: str
    dimension: str
    value: Any


class ProfileResponse(BaseModel):
    student_id: str
    dimensions: dict[str, Any]
    radar_data: list[float] = Field(default_factory=list)
    summary: str = ""
    version: int = 1


# === 评估 ===


class AssessmentResponse(BaseModel):
    student_id: str
    dimensions: dict[str, float]
    total_score: float
    level: str
    warnings: list[dict[str, Any]] = Field(default_factory=list)
