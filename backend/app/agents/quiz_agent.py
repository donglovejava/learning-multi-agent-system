"""Quiz Agent（练习题生成）。

分层练习题生成（§4.2.4）：默认 40% 基础 + 40% 中等 + 20% 提高。
答案正确率目标 100%（FR-018），支持交错练习（IN-09）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.json_utils import extract_json
from app.llm.spark_client import LLMError, SparkLLMClient

#: 难度分布（§4.2.4）
DIFFICULTY_DISTRIBUTION = {"easy": 0.4, "medium": 0.4, "hard": 0.2}

#: 难度中文标签，用于 Prompt
_DIFFICULTY_CN = {"easy": "基础", "medium": "中等", "hard": "提高"}


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
        LLM 返回后做结构校验，丢弃残缺项，保证答案字段齐全（FR-018）。
        """
        difficulty_cn = _DIFFICULTY_CN.get(difficulty, difficulty)
        system = (
            "你是命题专家，只输出 JSON，不要任何额外文字或解释。"
            "生成的题目必须答案准确无误。"
        )
        prompt = (
            f"为知识点「{knowledge}」生成 {n} 道{difficulty_cn}难度的单项选择题。\n"
            f"严格输出一个 JSON 数组，每个元素包含字段：\n"
            f'question(题干), options(4 个选项的字符串数组，以 "A. "/"B. " 开头), '
            f'answer(正确选项字母 A/B/C/D), explanation(解析), points(分值整数)。\n'
            f"只输出 JSON 数组本身。"
        )
        try:
            raw = await self.llm.chat(prompt, system=system, temperature=0.5)
        except LLMError:
            return []

        items = extract_json(raw)
        if not isinstance(items, list):
            return []

        questions: list[dict[str, Any]] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            normalized = self._normalize(item, knowledge, difficulty, idx)
            if normalized is not None:
                questions.append(normalized)
        return questions

    @staticmethod
    def _normalize(
        item: dict[str, Any], knowledge: str, difficulty: str, idx: int
    ) -> dict[str, Any] | None:
        """校验并补全单题；缺少题干/选项/答案则丢弃（保证答案字段齐全）。"""
        question = item.get("question")
        options = item.get("options")
        answer = item.get("answer")
        if not question or not isinstance(options, list) or len(options) < 2 or not answer:
            return None
        return {
            "id": f"q_{difficulty}_{idx}",
            "knowledge": knowledge,
            "difficulty": difficulty,
            "type": "multiple_choice",
            "question": str(question),
            "options": [str(o) for o in options],
            "answer": str(answer).strip()[:1].upper(),
            "explanation": str(item.get("explanation", "")),
            "points": int(item["points"]) if str(item.get("points", "")).isdigit() else 10,
            "time_limit": 120,
        }
