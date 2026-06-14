"""Assessment Agent（效果评估）。

10 维度加权评估 + 预警（§4.2.9 / §3.1.4）。综合得分驱动学习预警，
并与 Path Agent 联动触发路径调整（FR-033）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent

#: 10 个评估维度（§3.1.4）
DIMENSIONS = [
    "知识掌握度", "学习进度", "学习时长", "资源使用率", "练习正确率",
    "学习频率", "知识遗忘率", "深度学习能力", "学习主动性", "学习持续性",
]

#: 各维度权重，顺序对齐 DIMENSIONS（§3.1.4，合计 1.0）
WEIGHTS = [0.20, 0.15, 0.10, 0.10, 0.15, 0.05, 0.10, 0.05, 0.05, 0.05]

#: 各维度预警阈值，低于该值触发预警（§3.1.4）
WARNING_THRESHOLDS = {
    "知识掌握度": 0.60, "学习进度": 0.50, "学习时长": 0.50, "资源使用率": 0.40,
    "练习正确率": 0.50, "学习频率": 0.43, "知识遗忘率": 0.70, "深度学习能力": 0.40,
    "学习主动性": 0.20, "学习持续性": 0.60,
}


class AssessmentAgent(BaseAgent):
    """多维度学习效果评估。"""

    name = "assessment"

    def __init__(self, repo: Any) -> None:
        self.repo = repo

    async def run(self, state: AgentState) -> dict[str, Any]:
        student_id = state["student_id"]
        scores = await self._collect_scores(student_id)
        total = sum(scores[dim] * w for dim, w in zip(DIMENSIONS, WEIGHTS))
        warnings = [
            {"dimension": dim, "score": scores[dim], "threshold": WARNING_THRESHOLDS[dim]}
            for dim in DIMENSIONS
            if scores[dim] < WARNING_THRESHOLDS[dim]
        ]
        return {
            "assessment": {
                "type": "assessment",
                "dimensions": scores,
                "total_score": round(total, 4),
                "warnings": warnings,
                "level": self._level(total),
            }
        }

    async def _collect_scores(self, student_id: str) -> dict[str, float]:
        """从行为数据仓储计算各维度得分。骨架委派给 repo。"""
        return await self.repo.compute_assessment_dimensions(student_id, DIMENSIONS)

    @staticmethod
    def _level(total: float) -> str:
        if total > 0.8:
            return "优秀"
        if total > 0.6:
            return "良好"
        return "需改进"
