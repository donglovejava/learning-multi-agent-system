"""MindMap Agent（思维导图生成）。

优先从知识图谱提取节点构建层次结构；图谱不可用时用 LLM 生成知识点的
层次拆解，输出前端可渲染的 JSON（§4.2.5）。生成时间目标 ≤5s（FR-019）。
"""

from __future__ import annotations

from typing import Any, Optional

from app.agents.base import AgentState, BaseAgent
from app.llm.json_utils import extract_json
from app.llm.spark_client import LLMError, SparkLLMClient


class MindMapAgent(BaseAgent):
    """生成知识点思维导图。"""

    name = "mindmap"

    def __init__(self, llm: SparkLLMClient | None = None, graph_store: Any = None) -> None:
        self.llm = llm
        self.graph_store = graph_store

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        tree = await self._build_tree(knowledge)
        return {"mindmap": {"type": "mindmap", "data": tree}}

    async def _build_tree(self, knowledge: str) -> dict[str, Any]:
        """构建思维导图层次结构。

        优先用知识图谱真实关系；图谱为空且有 LLM 时由 LLM 拆解；
        两者都不可用则返回单节点占位。
        """
        # 接入 Neo4j 后：从 graph_store 按真实关系构建
        if self.graph_store is not None:
            tree = await self._from_graph(knowledge)
            if tree is not None:
                return tree

        if self.llm is not None:
            tree = await self._from_llm(knowledge)
            if tree is not None:
                return tree

        return self._fallback(knowledge)

    async def _from_graph(self, knowledge: str) -> Optional[dict[str, Any]]:
        """从知识图谱构建（接 Neo4j 后实现真实关系提取）。"""
        return None

    async def _from_llm(self, knowledge: str) -> Optional[dict[str, Any]]:
        """用 LLM 把知识点拆解为 2 层思维导图结构。"""
        system = (
            "你是知识结构专家，只输出 JSON，不要任何额外文字。"
        )
        prompt = (
            f"把知识点「{knowledge}」拆解成思维导图，输出一个 JSON 对象：\n"
            f'{{"root": {{"id": "根id", "label": "{knowledge}"}}, '
            f'"children": [{{"id": "子id", "label": "子主题", '
            f'"children": [{{"id": "孙id", "label": "要点"}}]}}]}}\n'
            f"生成 3-6 个一级子主题，每个含 2-4 个要点。只输出 JSON 本身。"
        )
        try:
            raw = await self.llm.chat(prompt, system=system, temperature=0.4)
        except LLMError:
            return None
        data = extract_json(raw)
        if isinstance(data, dict) and "root" in data:
            data.setdefault("children", [])
            return data
        return None

    @staticmethod
    def _fallback(knowledge: str) -> dict[str, Any]:
        """无图谱无 LLM 时的单节点占位。"""
        return {"root": {"id": knowledge, "label": knowledge}, "children": []}
