"""创新一：可解释 AI 决策（IN-03）。

知识图谱推理 + 自然语言生成：每个推荐都给出理由。
对应设计说明书 3.1 节。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


@dataclass
class RecommendationResult:
    recommendation: str
    explanation: str
    confidence: float
    reasoning_chain: List[str] = field(default_factory=list)
    weak_points: List[Dict] = field(default_factory=list)


class ExplainableRecommender:
    """可解释推荐系统。

    依赖一个知识图谱仓库对象（graph_repo），需提供
    `prerequisite_chain(target) -> List[Dict]`，返回 name/difficulty/category。
    解耦数据库实现，便于测试。
    """

    def __init__(self, graph_repo, weak_threshold: float = 0.6) -> None:
        self.graph_repo = graph_repo
        self.weak_threshold = weak_threshold

    def recommend_with_explanation(
        self,
        student_id: str,
        target_knowledge: str,
        profile: Dict[str, float],
    ) -> RecommendationResult:
        chain = self.graph_repo.prerequisite_chain(target_knowledge)
        if not chain:
            return RecommendationResult(
                recommendation=target_knowledge,
                explanation=f"未找到 {target_knowledge} 的前置知识，可以直接学习。",
                confidence=0.5,
            )

        weak_points = self._find_weak_points(chain, profile)
        reasoning_chain = [node["name"] for node in chain]

        if not weak_points:
            return RecommendationResult(
                recommendation=target_knowledge,
                explanation=f"推荐你直接学习 {target_knowledge}，因为你已掌握所有前置知识。",
                confidence=0.9,
                reasoning_chain=reasoning_chain,
            )

        weakest = weak_points[0]
        explanation = self._generate_explanation(target_knowledge, weakest, len(chain))
        result = RecommendationResult(
            recommendation=weakest["name"],
            explanation=explanation,
            confidence=self._calc_confidence(weak_points),
            reasoning_chain=reasoning_chain,
            weak_points=weak_points,
        )
        logger.debug("可解释推荐: %s -> %s", target_knowledge, result.recommendation)
        return result

    def explain_path_adjustment(
        self,
        original_path: List[str],
        new_path: List[str],
        assessment_data: Dict[str, Dict],
    ) -> str:
        added = set(new_path) - set(original_path)
        removed = set(original_path) - set(new_path)
        parts: List[str] = []
        for node in added:
            score = assessment_data.get(node, {}).get("score", 0)
            if score < 0.6:
                parts.append(f"检测到你在 {node} 章节得分 {score*100:.0f}%，所以增加了针对性练习")
        for node in removed:
            score = assessment_data.get(node, {}).get("score", 0)
            if score > 0.9:
                parts.append(f"你在 {node} 章节表现优秀（{score*100:.0f}%），所以跳过了重复内容")
        return "；".join(parts) if parts else "根据最新学习数据微调了路径顺序"

    def _find_weak_points(
        self, chain: List[Dict], profile: Dict[str, float]
    ) -> List[Dict]:
        weak = []
        for node in chain:
            mastery = profile.get(node["name"], 0.5)
            if mastery < self.weak_threshold:
                weak.append(
                    {
                        "name": node["name"],
                        "mastery": mastery,
                        "difficulty": node.get("difficulty", 3),
                        "category": node.get("category", ""),
                    }
                )
        weak.sort(key=lambda x: x["mastery"])
        return weak

    def _generate_explanation(
        self, target: str, weak_point: Dict, chain_length: int
    ) -> str:
        name = weak_point["name"]
        mastery_pct = weak_point["mastery"] * 100
        explanation = (
            f"推荐你先学 {name}，因为你的 {name} 基础薄弱"
            f"（掌握度 {mastery_pct:.0f}%），而它是学习 {target} 的必要前置知识。"
        )
        if chain_length > 2:
            explanation += f"掌握 {name} 后，后续学习会更顺利。"
        difficulty = weak_point["difficulty"]
        if difficulty >= 4:
            explanation += "这个知识点难度较高，建议多花时间理解。"
        elif difficulty <= 2:
            explanation += "这个知识点相对基础，可以快速掌握。"
        return explanation

    def _calc_confidence(self, weak_points: List[Dict]) -> float:
        if not weak_points:
            return 0.9
        avg = sum(wp["mastery"] for wp in weak_points) / len(weak_points)
        return min(0.5 + avg * 0.5, 0.95)
