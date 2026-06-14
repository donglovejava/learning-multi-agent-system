"""Video Agent（视频生成）。

调用 SeeDance 生成教学视频/动画（§4.2.6）。视频生成耗时 3-5 分钟，
采用异步任务 + 进度追踪（TC-002 / §4.5.1），先返回 task_id，后续轮询状态。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.seedance_client import SeeDanceClient
from app.llm.spark_client import SparkLLMClient


class VideoAgent(BaseAgent):
    """生成教学视频（异步）。"""

    name = "video"

    def __init__(self, seedance: SeeDanceClient, llm: SparkLLMClient) -> None:
        self.seedance = seedance
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        script = await self._generate_script(knowledge)
        task = await self.seedance.submit_task(script=script, style="educational", duration=90)
        return {
            "video": {
                "type": "video",
                "task_id": task.get("task_id"),
                "status": "processing",
            }
        }

    async def _generate_script(self, knowledge: str) -> str:
        """用 LLM 生成 90 秒教学视频脚本。"""
        prompt = f"为知识点「{knowledge}」编写一段 90 秒教学动画脚本，分镜清晰、讲解准确。"
        return await self.llm.chat(prompt)
