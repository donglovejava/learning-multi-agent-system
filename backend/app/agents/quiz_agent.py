"""Quiz Agent（练习题生成）。

分层练习题生成（§4.2.4）：默认 40% 基础 + 40% 中等 + 20% 提高。
答案正确率目标 100%（FR-018），支持交错练习（IN-09）。
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.json_utils import extract_json
from app.llm.spark_client import LLMError, SparkLLMClient

logger = logging.getLogger(__name__)

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
            f"严格输出一个 JSON 数组，不要代码块标记，每个元素包含字段：\n"
            f'question(题干), options(4个选项的字符串数组，不加字母前缀), '
            f'answer(正确选项字母 A/B/C/D，必须是单个大写字母), explanation(解析)。\n'
            f"答案字段 answer 必须是单个大写字母，不要写选项内容。只输出 JSON 数组本身。"
        )
        try:
            raw = await self.llm.chat(prompt, system=system, temperature=0.5)
        except LLMError:
            return []

        try:
            items = extract_json(raw)
        except ValueError:
            logger.warning("题目 JSON 解析失败，原始输出：%s", raw[:200])
            return []
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
        """校验并补全单题；缺少题干/选项/答案则丢弃（保证答案字段齐全）。

        容错处理 LLM 常见格式问题：
        - answer 为 "A. xxx" / "A" / 1（数字）等，统一规整为字母 A/B/C/D
        - answer 为数字索引时转成对应字母
        - options 未带 "A. " 前缀时补上
        """
        import re

        question = item.get("question")
        options = item.get("options")
        answer = item.get("answer")
        if not question or not isinstance(options, list) or len(options) < 2:
            return None

        # 规整 options：保证每个都以 "A. "/"B. " 前缀
        letters = ["A", "B", "C", "D", "E"]
        norm_options = []
        for i, opt in enumerate(options):
            opt_str = str(opt).strip()
            # 已有 "A. " 前缀就保留
            if re.match(r"^[A-E][.、\)．]", opt_str):
                norm_options.append(opt_str)
            else:
                norm_options.append(f"{letters[i]}. {opt_str}" if i < len(letters) else opt_str)

        # 规整 answer
        norm_answer: str | None = None
        if isinstance(answer, int) and 0 <= answer < len(norm_options):
            norm_answer = letters[answer]
        elif isinstance(answer, str):
            answer_str = answer.strip()
            # "A" / "A. xxx" / "(A)" → 取首字母
            m = re.search(r"([A-E])", answer_str)
            if m and len(answer_str) <= 3:
                norm_answer = m.group(1)
            elif m:
                # "A. 自然语言处理" 这种，首字母明确
                norm_answer = m.group(1)
            else:
                # 答案是选项文本本身，匹配选项
                for i, opt in enumerate(norm_options):
                    # 去掉前缀 "A. " 后比较
                    opt_text = re.sub(r"^[A-E][.、\)．]\s*", "", opt).strip()
                    if answer_str == opt_text or answer_str in opt or opt_text in answer_str:
                        norm_answer = letters[i] if i < len(letters) else None
                        break

        if not norm_answer:
            return None

        return {
            "id": f"q_{difficulty}_{idx}",
            "knowledge": knowledge,
            "difficulty": difficulty,
            "type": "multiple_choice",
            "question": str(question),
            "options": norm_options,
            "answer": norm_answer,
            "explanation": str(item.get("explanation", "")),
            "points": int(item["points"]) if str(item.get("points", "")).isdigit() else 10,
            "time_limit": 120,
        }
