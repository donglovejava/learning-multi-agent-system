"""Quiz Agent（练习题生成）。

分层练习题生成（§4.2.4）：默认 40% 基础 + 40% 中等 + 20% 提高。
答案正确率目标 100%（FR-018），支持交错练习（IN-09）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import SparkLLMClient

#: 难度分布（§4.2.4）
DIFFICULTY_DISTRIBUTION = {"easy": 0.4, "medium": 0.4, "hard": 0.2}


class QuizAgent(BaseAgent):
    """生成分层练习题。"""

    name = "quiz"

    def __init__(self, llm: SparkLLMClient) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        profile = state.get("profile", {})
        result = await self.generate(knowledge, profile, count=10)
        return {"quiz": result}

    async def generate(
        self, knowledge: str, profile: dict[str, Any], count: int = 10
    ) -> dict[str, Any]:
        """按难度分布生成 count 道题。"""
        questions: list[dict[str, Any]] = []
        for difficulty, ratio in DIFFICULTY_DISTRIBUTION.items():
            n = max(1, int(count * ratio))
            batch = await self._generate_batch(knowledge, difficulty, n, profile)
            questions.extend(batch)
        return {"type": "quiz", "questions": questions, "total": len(questions)}

    async def _generate_batch(
        self, knowledge: str, difficulty: str, n: int, profile: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """生成单一难度的一批题目。

        输出遵循题目 JSON Schema（§4.2.4）：
        id/knowledge/difficulty/type/question/options/answer/explanation/points/time_limit。
        """
        raise NotImplementedError("待接入 LLM 生成题目并校验答案正确性")
