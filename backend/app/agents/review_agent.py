"""Review Agent（内容审核）。

5 层防幻觉审核（§4.2.10 / 附录 A IN-04）。对其他 Agent 产出的内容做
检索验证、逻辑一致性、事实核查、敏感检测，任一 error/critical 即拒绝放行。
目标审核准确率 >95%（FR-022）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import SparkLLMClient

#: 审核问题严重级别，error/critical 会导致内容不通过
SEVERITY_BLOCKING = {"error", "critical"}


class ReviewAgent(BaseAgent):
    """生成内容质量审核（5 层防线）。"""

    name = "review"

    def __init__(self, llm: SparkLLMClient) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        # 收集本轮需审核的资源产出
        targets = {
            key: state[key]
            for key in ("document", "quiz", "mindmap", "code")
            if state.get(key)
        }
        references = state.get("retrieved_context", [])
        results = {}
        for key, content in targets.items():
            results[key] = await self.review(content, references)
        passed = all(r["passed"] for r in results.values()) if results else True
        return {"review_result": {"passed": passed, "details": results}}

    async def review(self, content: dict[str, Any], references: list[dict[str, Any]]) -> dict[str, Any]:
        """对单份内容执行 5 层审核，汇总问题与质量分。"""
        issues: list[dict[str, str]] = []
        # 第 1 道：知识检索验证（是否有出处支撑）
        if not references:
            issues.append({"type": "unverified", "severity": "warning"})
        # 第 2-4 道：逻辑/事实/敏感由 LLM 核查（骨架占位）
        # 第 5 道：结构完整性等可在此扩展
        passed = not any(i["severity"] in SEVERITY_BLOCKING for i in issues)
        return {
            "passed": passed,
            "issues": issues,
            "quality_score": self._quality_score(issues),
        }

    @staticmethod
    def _quality_score(issues: list[dict[str, str]]) -> float:
        """按问题严重度扣分，得到 0-1 质量分。"""
        penalty = {"warning": 0.1, "error": 0.4, "critical": 1.0}
        score = 1.0 - sum(penalty.get(i["severity"], 0.0) for i in issues)
        return max(0.0, round(score, 3))
