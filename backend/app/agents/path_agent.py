"""Path Agent（路径规划）。

基于知识图谱 DAG + 改进 Dijkstra，结合画像规划学习路径（§4.2.8 / §7.4）。
路径附带可解释推荐理由（IN-03），并嵌入个性化复习节点（IN-04）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.innovations.explainable_recommender import ExplainableRecommender


def improved_dijkstra(
    dag: dict[str, dict[str, float]],
    start: str,
    end: str,
    profile: dict[str, float],
) -> list[str]:
    """改进 Dijkstra：按画像掌握度调整边权（§7.4.1）。

    掌握度越高，对应节点权重越低，倾向跳过已掌握内容。
    """
    import heapq

    distances = {node: float("inf") for node in dag}
    distances[start] = 0.0
    previous: dict[str, str | None] = {node: None for node in dag}
    pq: list[tuple[float, str]] = [(0.0, start)]

    while pq:
        current_dist, current = heapq.heappop(pq)
        if current == end:
            break
        for neighbor, base_weight in dag.get(current, {}).items():
            mastery = profile.get(neighbor, 0.5)
            adjusted = base_weight * (1.5 - mastery)
            dist = current_dist + adjusted
            if dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = dist
                previous[neighbor] = current
                heapq.heappush(pq, (dist, neighbor))

    path: list[str] = []
    node: str | None = end
    while node is not None:
        path.append(node)
        node = previous.get(node)
    return path[::-1]


class PathAgent(BaseAgent):
    """规划个性化学习路径。"""

    name = "path"

    def __init__(self, graph_repo: Any, recommender: ExplainableRecommender | None = None) -> None:
        self.graph_repo = graph_repo
        self.recommender = recommender

    async def run(self, state: AgentState) -> dict[str, Any]:
        target = state["knowledge_point"]
        profile = state.get("profile", {})
        # 从图谱仓储取得目标子图（DAG），骨架阶段交由 repo 实现
        dag = await self.graph_repo.get_subgraph(target, max_depth=5)
        path = improved_dijkstra(dag, start=self._entry(dag), end=target, profile=profile)
        explanation = None
        if self.recommender is not None:
            result = self.recommender.recommend_with_explanation(
                state["student_id"], target, profile
            )
            explanation = result.explanation
        return {
            "path": {
                "type": "path",
                "nodes": path,
                "total_nodes": len(path),
            },
            "explanation": explanation,
        }

    @staticmethod
    def _entry(dag: dict[str, dict[str, float]]) -> str:
        """选取入口节点（无前驱者）。骨架取首个键，接图谱后按入度计算。"""
        return next(iter(dag), "current")
