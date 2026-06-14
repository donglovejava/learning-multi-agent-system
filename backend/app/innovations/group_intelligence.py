"""群体智能优化（IN-02, P1）。

利用所有学生的匿名学习序列，挖掘"先学 A 再学 B 成功率高"的群体规律，
并据此优化个体学习路径的节点顺序。

设计依据：设计说明书 §3.5。
"""

from __future__ import annotations

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class GroupIntelligenceOptimizer:
    """群体智能优化器。

    依赖一个数据访问对象 ``db``，需提供：

    - ``get_all_learning_sequences()`` -> list[list[dict]]
      每条序列为按时间排序的学习事件，事件含 knowledge_id / score。
    - ``get_high_quality_patterns()`` -> list[dict]
      已挖掘出的高质量模式（from / to / success_rate / support）。
    """

    _DEFAULT_MIN_SUPPORT = 100
    _SUCCESS_SCORE = 0.7
    _SUCCESS_RATE_THRESHOLD = 0.75

    def __init__(self, db) -> None:
        self.db = db

    def analyze_patterns(self, min_support: int = _DEFAULT_MIN_SUPPORT) -> list[dict]:
        """分析群体学习模式，返回按成功率降序的规律列表。"""
        all_sequences = self.db.get_all_learning_sequences()
        pair_stats: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: {"total": 0, "success": 0}
        )

        for seq in all_sequences:
            for i in range(len(seq) - 1):
                a, b = seq[i]["knowledge_id"], seq[i + 1]["knowledge_id"]
                pair_stats[(a, b)]["total"] += 1
                if seq[i + 1]["score"] > self._SUCCESS_SCORE:
                    pair_stats[(a, b)]["success"] += 1

        patterns: list[dict] = []
        for (a, b), stats in pair_stats.items():
            if stats["total"] < min_support:
                continue
            success_rate = stats["success"] / stats["total"]
            if success_rate > self._SUCCESS_RATE_THRESHOLD:
                patterns.append(
                    {
                        "from": a,
                        "to": b,
                        "success_rate": success_rate,
                        "support": stats["total"],
                    }
                )

        patterns.sort(key=lambda x: x["success_rate"], reverse=True)
        logger.info("群体模式挖掘完成，命中 %d 条高质量规律", len(patterns))
        return patterns

    def optimize_path(self, student_id: str, candidate_path: list[str]) -> list[str]:
        """用群体规律优化个体路径的相邻节点顺序。"""
        patterns = self.db.get_high_quality_patterns()
        optimized = list(candidate_path)
        for i in range(len(optimized) - 1):
            for pattern in patterns:
                # 若当前顺序与高质量规律相反，则交换
                if optimized[i] == pattern["to"] and optimized[i + 1] == pattern["from"]:
                    optimized[i], optimized[i + 1] = optimized[i + 1], optimized[i]
                    break
        return optimized
