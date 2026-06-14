"""Orchestrator Agent（总指挥）：意图识别与任务分发（§4.2.1）。"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import SparkLLMClient


class OrchestratorAgent(BaseAgent):
    """分析用户意图，决定路由到哪些下游 Agent。

    意图标签：build_profile / generate_resource / plan_path / assess / chat
    """

    name = "orchestrator"

    # 意图 → 默认资源类型映射
    DEFAULT_RESOURCE_TYPES = ["document", "quiz", "mindmap"]

    def __init__(self, llm: SparkLLMClient) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        user_input = state.get("user_input", "")
        intent = state.get("intent") or await self.llm.classify_intent(user_input)

        update: dict[str, Any] = {"intent": intent}

        if intent == "generate_resource":
            # 抽取知识点；若上层已给定则沿用
            knowledge = state.get("knowledge_point") or await self._extract_knowledge(user_input)
            update["knowledge_point"] = knowledge
            update.setdefault(
                "resource_types", state.get("resource_types") or self.DEFAULT_RESOURCE_TYPES
            )
        return update

    async def _extract_knowledge(self, user_input: str) -> str:
        """从自然语言中抽取目标知识点（§4.2.1）。占位待接入 LLM。"""
        raise NotImplementedError("知识点抽取待接入 LLM extract_knowledge")
