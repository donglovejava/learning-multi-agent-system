"""Retrieval Agent（知识检索）。

双引擎检索：向量（Milvus）+ 图谱（Neo4j），RRF 融合（§4.2.11 / §6.3 / §6.4）。
检索延迟目标 <1s（PM-009）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import SparkLLMClient


class RetrievalAgent(BaseAgent):
    """知识库双引擎检索与增强。"""

    name = "retrieval"

    def __init__(
        self,
        llm: SparkLLMClient,
        vector_store: Any = None,
        graph_store: Any = None,
    ) -> None:
        self.llm = llm
        self.vector_store = vector_store  # Milvus 客户端（待接入）
        self.graph_store = graph_store    # Neo4j 客户端（待接入）

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state.get("knowledge_point") or state.get("user_input", "")
        context = await self.search(query, top_k=5)
        return {"retrieved_context": context}

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """向量 + 图谱双引擎检索，RRF 融合后取 top_k。

        容错：query 非字符串、或两路引擎都不可用时返回空，不中断主流程。
        """
        if not isinstance(query, str) or not query:
            return []
        try:
            vector_hits = await self._vector_search(query, top_k)
            graph_hits = await self._graph_search(query, top_k)
        except Exception:
            return []
        merged = self._rrf_merge(vector_hits, graph_hits, k=60)
        return merged[:top_k]

    async def _vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """向量检索：embedding → Milvus ANN（HNSW/COSINE，§6.3）。

        向量化或向量库未接入时优雅降级为空结果（检索退化为"无外部知识"），
        不中断主流程（§4.5.2）。
        """
        if self.vector_store is None:
            return []
        try:
            vector = await self.llm.embed(query)
        except NotImplementedError:
            return []
        return await self.vector_store.search(vector, top_k)

    async def _graph_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """图谱检索：实体抽取 → 图谱节点查询（§6.4）。

        graph_store 提供 async search/query_entities；不可用时返回空。
        """
        if self.graph_store is None:
            return []
        # 优先用 search（关键词匹配），回退 query_entities
        method = getattr(self.graph_store, "search", None)
        try:
            if method is not None:
                result = method(query, top_k)
                if hasattr(result, "__await__"):
                    result = await result
                return result or []
            entities = await self._extract_entities(query)
            qe = getattr(self.graph_store, "query_entities", None)
            if qe is None:
                return []
            result = qe(entities, top_k)
            if hasattr(result, "__await__"):
                result = await result
            return result or []
        except Exception:
            return []

    @staticmethod
    def _rrf_merge(
        vector_hits: list[dict[str, Any]],
        graph_hits: list[dict[str, Any]],
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """Reciprocal Rank Fusion 融合两路检索结果（§4.2.11）。

        score(d) = Σ 1 / (k + rank_i(d))，按融合得分降序。
        """
        scores: dict[str, float] = {}
        by_id: dict[str, dict[str, Any]] = {}
        for hits in (vector_hits, graph_hits):
            for rank, item in enumerate(hits):
                key = str(item.get("id"))
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
                by_id.setdefault(key, item)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [{**by_id[key], "rrf_score": score} for key, score in ranked]

    async def _extract_entities(self, query: str) -> list[str]:
        """从查询抽取知识实体；骨架返回原查询。"""
        return [query]
