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
        # 从图谱仓储取得目标子图（DAG）
        dag = await self._get_subgraph(target, max_depth=5)
        if not dag or len(dag) <= 1:
            # 知识点不在图谱中：返回单节点路径 + 占位解释
            return {
                "path": {
                    "type": "path",
                    "nodes": [target],
                    "total_nodes": 1,
                    "note": "该知识点暂未在知识图谱中，无可推荐前置路径",
                },
                "explanation": f"「{target}」暂未在知识图谱中，建议直接学习。",
            }
        path = improved_dijkstra(dag, start=self._entry(dag), end=self._resolve_target(dag, target), profile=profile)
        explanation = None
        if self.recommender is not None:
            try:
                result = self.recommender.recommend_with_explanation(
                    state["student_id"], target, self._profile_to_mastery(profile)
                )
                explanation = result.explanation
            except Exception:
                pass
        # 路径节点附加难度/类别信息，供前端展示
        enriched = [self._enrich_node(n) for n in path]
        return {
            "path": {
                "type": "path",
                "nodes": enriched,
                "total_nodes": len(enriched),
                "target": target,
            },
            "explanation": explanation,
        }

    async def _get_subgraph(self, target: str, max_depth: int) -> dict[str, dict[str, float]]:
        """兼容 sync/async 的 get_subgraph。"""
        method = getattr(self.graph_repo, "get_subgraph", None)
        if method is None:
            return {}
        result = method(target, max_depth)
        if hasattr(result, "__await__"):
            result = await result
        return result

    def _resolve_target(self, dag: dict[str, dict[str, float]], target: str) -> str:
        """目标节点可能在图谱中是模糊匹配后的精确名。"""
        if target in dag:
            return target
        # 找一个名字包含 target 的节点
        for node in dag:
            if target in node or node in target:
                return node
        return target

    def _entry(self, dag: dict[str, dict[str, float]]) -> str:
        """选取入口节点（无前驱者）；回退首个节点。"""
        if hasattr(self.graph_repo, "get_entry_nodes"):
            entries = self.graph_repo.get_entry_nodes()
            in_dag = [e for e in entries if e in dag]
            if in_dag:
                return in_dag[0]
        return next(iter(dag), "current")

    def _enrich_node(self, name: str) -> dict[str, Any]:
        """给路径节点附加难度/类别信息。"""
        node = None
        if hasattr(self.graph_repo, "get_node"):
            node = self.graph_repo.get_node(name)
        if node is None:
            return {"id": name, "label": name}
        return {
            "id": node.get("id", name),
            "label": node.get("name", name),
            "difficulty": node.get("difficulty"),
            "category": node.get("category"),
            "description": node.get("description"),
        }

    @staticmethod
    def _profile_to_mastery(profile: dict[str, Any]) -> dict[str, float]:
        """把画像转成可解释推荐需要的 {知识点: 掌握度}。"""
        mastery: dict[str, float] = {}
        # 通用：用 knowledge_base 作为所有知识点基线掌握度
        base = profile.get("knowledge_base")
        if isinstance(base, (int, float)):
            mastery["_default"] = float(base)
        return mastery
