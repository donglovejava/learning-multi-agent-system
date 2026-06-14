"""MindMap Agent（思维导图生成）。

从知识图谱提取相关节点，构建层次树 → 前端可渲染 JSON（§4.2.5）。
生成时间目标 ≤5s（FR-019）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent


class MindMapAgent(BaseAgent):
    """生成知识点思维导图。"""

    name = "mindmap"

    def __init__(self, graph_store: Any = None) -> None:
        self.graph_store = graph_store  # Neo4j 客户端（待接入）

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        tree = await self.generate(knowledge)
        return {"mindmap": tree}

    async def generate(self, knowledge: str, depth: int = 2) -> dict[str, Any]:
        """提取知识图谱子图并构建层次树（§4.2.5）。"""
        nodes = await self._get_related_nodes(knowledge, depth)
        tree = self._build_tree(knowledge, nodes)
        return {"type": "mindmap", "data": tree}

    async def _get_related_nodes(self, knowledge: str, depth: int) -> list[dict[str, Any]]:
        if self.graph_store is None:
            return []
        return await self.graph_store.get_related_nodes(knowledge, depth)

    def _build_tree(self, root: str, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        """将图谱节点组织为 {root, children} 层次结构（§4.2.5）。"""
        return {"root": {"id": root, "label": root}, "children": []}
