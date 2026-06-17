"""知识图谱仓库（种子数据实现，可平滑迁移到 Neo4j）。

提供 ExplainableRecommender / PathAgent / MindMapAgent / RetrievalAgent
所需的真实图谱查询接口。当前基于内置种子数据（knowledge_seed），
后续可在 methods/ 目录新增 Neo4j 实现，保持同名签名替换即可。

§6.4 节点 Knowledge(name/difficulty/category/description)，关系 PREREQUISITE。
"""

from __future__ import annotations

from collections import deque
from typing import Any

from app.core.config import settings
from app.db.knowledge_seed import (
    SEED_NODES,
    build_adjacency,
    fuzzy_match,
    all_node_names,
)
import logging

logger = logging.getLogger(__name__)


class KnowledgeGraphRepo:
    """知识图谱仓库。

    优先连 Neo4j（若已配置且可连接），否则回退内置种子数据。
    所有查询方法签名与未来 Neo4j 实现保持一致。
    """

    def __init__(self) -> None:
        self._driver = None  # Neo4j driver（懒加载）
        self._use_neo4j = False
        # 种子数据索引
        self._forward, self._backward, self._nodes = build_adjacency()

    # --- 连接管理 -----------------------------------------------------------

    def _ensure_neo4j(self) -> bool:
        """尝试连接 Neo4j；不可用则回退种子数据。"""
        if self._use_neo4j or self._driver is not None:
            return self._use_neo4j
        try:
            from neo4j import GraphDatabase  # type: ignore
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            self._driver.verify_connectivity()
            self._use_neo4j = True
            logger.info("知识图谱已连接 Neo4j")
        except Exception as exc:
            logger.info("Neo4j 不可用(%s)，使用内置种子图谱", str(exc)[:60])
            self._use_neo4j = False
        return self._use_neo4j

    # --- ExplainableRecommender 接口（同步）-------------------------------

    def prerequisite_chain(self, target: str, max_depth: int = 8) -> list[dict[str, Any]]:
        """查询目标知识点的前置知识链（含传递前置），按距离排序。

        返回 [{name, difficulty, category, depth, strength}]。
        """
        # 名字模糊匹配
        matched = fuzzy_match(target) or target
        if matched not in self._nodes:
            return []

        visited: dict[str, dict] = {}
        queue: deque[tuple[str, int, float]] = deque([(matched, 0, 1.0)])

        while queue:
            node, depth, strength = queue.popleft()
            if depth >= max_depth:
                continue
            for prereq, edge_strength in self._backward.get(node, []):
                if prereq in visited:
                    continue
                node_info = self._nodes.get(prereq, {})
                visited[prereq] = {
                    "name": prereq,
                    "difficulty": node_info.get("difficulty", 3),
                    "category": node_info.get("category", ""),
                    "depth": depth + 1,
                    "strength": edge_strength,
                }
                queue.append((prereq, depth + 1, strength * edge_strength))

        result = list(visited.values())
        result.sort(key=lambda x: x["depth"])
        return result

    # --- PathAgent 接口 ----------------------------------------------------

    def get_subgraph(self, target: str, max_depth: int = 5) -> dict[str, dict[str, float]]:
        """获取以 target 为终点的子图（DAG），返回邻接表。

        格式：{node_name: {neighbor_name: weight}}
        weight 由前置强度决定，掌握度由调用方（PathAgent）注入。
        """
        matched = fuzzy_match(target) or target
        if matched not in self._nodes:
            return {matched: {}}

        # 收集 target 的所有前置（含传递）+ target 自身
        chain_nodes = {n["name"] for n in self.prerequisite_chain(matched, max_depth)}
        chain_nodes.add(matched)

        # 构建子图邻接表：只保留 chain_nodes 内部的边
        subgraph: dict[str, dict[str, float]] = {}
        for node in chain_nodes:
            subgraph[node] = {}
            for succ, strength in self._forward.get(node, []):
                if succ in chain_nodes:
                    # 边权 = 难度系数 × 前置强度（掌握度由调用方再调整）
                    difficulty = self._nodes.get(succ, {}).get("difficulty", 3)
                    subgraph[node][succ] = difficulty * (1.2 - strength * 0.4)
        return subgraph

    # --- MindMapAgent 接口 -------------------------------------------------

    async def get_related_nodes(self, knowledge: str, depth: int = 2) -> list[dict[str, Any]]:
        """获取知识点相关节点（前后继），构建思维导图层次。"""
        matched = fuzzy_match(knowledge) or knowledge
        if matched not in self._nodes:
            return []

        root_node = self._nodes[matched]
        result = [root_node]

        # 一层后继
        for succ, strength in self._forward.get(matched, [])[:6]:
            if succ in self._nodes:
                result.append(self._nodes[succ])

        # 一层前置（作为"预备知识"）
        prereqs = [p for p, _ in self._backward.get(matched, [])][:4]
        for pre in prereqs:
            if pre in self._nodes:
                result.append(self._nodes[pre])

        return result

    async def get_children(self, knowledge: str) -> list[dict[str, Any]]:
        """获取直接后继知识点（思维导图子节点）。"""
        matched = fuzzy_match(knowledge) or knowledge
        children = []
        for succ, strength in self._forward.get(matched, []):
            if succ in self._nodes:
                children.append({**self._nodes[succ], "strength": strength})
        return children

    # --- RetrievalAgent 图检索接口 -----------------------------------------

    async def query_entities(self, entities: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        """根据实体名称查询图谱节点（图谱检索路）。"""
        results = []
        seen = set()
        for ent in entities:
            matched = fuzzy_match(ent)
            if matched and matched not in seen:
                seen.add(matched)
                results.append({**self._nodes[matched], "id": matched})
        return results[:top_k]

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """图谱检索：关键词匹配知识点（向量化未接入时的图检索兜底）。"""
        q = query.lower()
        scored = []
        for name, node in self._nodes.items():
            score = 0.0
            name_lower = name.lower()
            # 名字匹配权重最高
            if q in name_lower or name_lower in q:
                score += 1.0
            # 描述匹配
            desc = node.get("description", "").lower()
            if q in desc:
                score += 0.5
            # 分词匹配
            for token in q.split():
                if token in name_lower or token in desc:
                    score += 0.3
            if score > 0:
                scored.append((score, {**node, "id": name}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    # --- 工具方法 -----------------------------------------------------------

    def get_node(self, name: str) -> dict[str, Any] | None:
        """获取单个知识点信息。"""
        matched = fuzzy_match(name)
        if matched:
            return {**self._nodes[matched], "id": matched}
        return None

    def get_entry_nodes(self) -> list[str]:
        """获取 DAG 的入口节点（无前置），作为路径规划起点。"""
        return [name for name in self._nodes if name not in self._backward]

    def all_nodes(self) -> list[dict[str, Any]]:
        """返回所有种子节点。"""
        return [{**n, "id": n["name"]} for n in SEED_NODES]

    def all_edges(self) -> list[dict[str, Any]]:
        """返回所有前置边（供前端图谱可视化）。"""
        from app.db.knowledge_seed import SEED_EDGES
        return [{"source": pre, "target": succ, "strength": strength}
                for pre, succ, strength in SEED_EDGES]

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None


# 模块级单例（避免每次查询重建索引）
_repo_instance: KnowledgeGraphRepo | None = None


def get_graph_repo() -> KnowledgeGraphRepo:
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = KnowledgeGraphRepo()
    return _repo_instance
