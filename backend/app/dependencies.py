"""依赖装配容器（§2.1 / §4）。

集中构造单例：LLM 客户端、创新模块、11 个 Agent、编排图。
FastAPI 通过 ``get_orchestration`` 注入，避免每请求重复构造。

骨架阶段：图谱/向量/DB 仓储以占位对象注入，接入真实存储时替换工厂即可，
对 Agent 与路由层透明。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.agents.assessment_agent import AssessmentAgent
from app.agents.code_agent import CodeAgent
from app.agents.document_agent import DocumentAgent
from app.agents.graph import AgentRegistry, build_graph
from app.agents.mindmap_agent import MindMapAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.path_agent import PathAgent
from app.agents.profile_agent import ProfileAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.review_agent import ReviewAgent
from app.agents.video_agent import VideoAgent
from app.core.config import settings
from app.innovations.explainable_recommender import ExplainableRecommender
from app.innovations.scaffold_generator import ScaffoldGenerator
from app.llm.seedance_client import SeeDanceClient
from app.llm.spark_client import SparkLLMClient


class _PlaceholderRepo:
    """占位仓储：接入真实 Neo4j/Milvus/DB 前的桩。

    所有方法返回空结构，保证编排流程可端到端运行而不抛错。
    替换为真实仓储时保持同名异步方法签名即可。
    """

    async def get_subgraph(self, target: str, max_depth: int = 5) -> dict[str, dict[str, float]]:
        return {target: {}}

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return []

    async def query_entities(self, entities: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        """图谱实体查询（供 RetrievalAgent 图检索路）。接 Neo4j 后替换。"""
        return []

    def prerequisite_chain(self, target: str) -> list[dict[str, Any]]:
        """前置知识链（供 ExplainableRecommender 同步查询）。接 Neo4j 后替换。"""
        return []

    async def get_or_create(self, student_id: str) -> dict[str, Any]:
        """加载/初始化学生画像（供 Profile Agent）。接 PostgreSQL 后替换。"""
        return {}


@lru_cache
def _get_repo() -> _PlaceholderRepo:
    """共享占位仓储单例（图谱/向量/DB 的统一桩）。"""
    return _PlaceholderRepo()


@lru_cache
def get_llm() -> SparkLLMClient:
    return SparkLLMClient()


@lru_cache
def get_seedance() -> SeeDanceClient:
    return SeeDanceClient()


@lru_cache
def get_recommender() -> ExplainableRecommender:
    return ExplainableRecommender(_get_repo())


@lru_cache
def get_scaffold() -> ScaffoldGenerator:
    return ScaffoldGenerator(get_llm())


@lru_cache
def build_registry() -> AgentRegistry:
    """构造并注册全部 11 个 Agent。

    各 Agent 的依赖（LLM / SeeDance / 创新模块 / 占位仓储）在此统一注入，
    构造签名与各 Agent 模块保持一致。
    """
    llm = get_llm()
    repo = _get_repo()
    registry = AgentRegistry()
    for agent in (
        OrchestratorAgent(llm),
        ProfileAgent(llm, repo),
        RetrievalAgent(llm, repo, repo),
        DocumentAgent(llm, get_scaffold()),
        QuizAgent(llm),
        MindMapAgent(repo),
        CodeAgent(llm),
        VideoAgent(get_seedance(), llm),
        PathAgent(repo, get_recommender()),
        AssessmentAgent(repo),
        ReviewAgent(llm),
    ):
        registry.register(agent)
    return registry


@lru_cache
def get_orchestration() -> Any:
    """返回编排图（LangGraph 或回退实现），暴露 ``invoke(state)``。"""
    return build_graph(build_registry())
