"""Profile Agent（画像构建）。

职责：6 维度学习画像的构建与动态更新（§4.2.2）。
对话抽取 + EWMA 动态更新（§7.3.1），结合元认知/遗忘曲线创新。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.innovations.metacognition import ewma_update
from app.llm.spark_client import SparkLLMClient


class ProfileAgent(BaseAgent):
    """构建并维护学生 6 维度画像。"""

    name = "profile"

    #: 6 个画像维度（§3.1.1 / §4.2.2）
    DIMENSIONS = ["专业", "学习目标", "知识基础", "学习风格", "学习动机", "元认知"]

    def __init__(self, llm: SparkLLMClient, repo: Any = None) -> None:
        self.llm = llm
        self.repo = repo  # 画像持久化仓储（待接入，§6.1.1 student_profiles）

    async def run(self, state: AgentState) -> dict[str, Any]:
        """读取已有画像；若无则触发对话式构建。

        资源生成流程中此 Agent 仅负责加载画像供下游使用。
        """
        student_id = state["student_id"]
        profile = await self._load_profile(student_id)
        return {"profile": profile}

    async def process_reply(self, student_id: str, user_message: str, history: list) -> dict[str, Any]:
        """对话式画像构建单轮处理（§4.2.2）。

        抽取信息 → 更新画像 → 决定下一个问题；维度齐全则收尾。
        """
        extracted = await self.llm.extract_profile_info(user_message)  # 待接入
        profile = await self._load_profile(student_id)
        profile.update(extracted)

        missing = [d for d in self.DIMENSIONS if not profile.get(d)]
        if not missing:
            return {"done": True, "profile": profile}

        question = await self._generate_question(missing, profile)
        return {"done": False, "question": question, "profile": profile}

    def update_dimension(self, old: float, observed: float, alpha: float = 0.3) -> float:
        """对数值型维度（如知识基础）做 EWMA 更新（§7.3.1）。"""
        return ewma_update(old, observed, alpha)

    async def _load_profile(self, student_id: str) -> dict[str, Any]:
        """加载画像；骨架返回空画像，接入仓储后替换。"""
        if self.repo is not None:
            return await self.repo.get_or_create(student_id)
        return {}

    async def _generate_question(self, missing: list[str], profile: dict[str, Any]) -> str:
        """针对缺失维度生成下一个引导问题。"""
        raise NotImplementedError("待接入 LLM 生成画像引导问题")
