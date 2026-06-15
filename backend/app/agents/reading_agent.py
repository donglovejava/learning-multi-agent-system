"""Reading Agent（拓展阅读材料生成）。

生成知识点的拓展阅读材料：前沿延伸、相关论文/资源线索、深入方向（§3.1.2）。
输出 Markdown，生成时间目标 ≤15s（FR-016 资源类型表）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import LLMError, SparkLLMClient

#: 拓展阅读结构模板（引导 LLM 输出）
READING_TEMPLATE = """## 延伸主题
## 推荐阅读方向
## 相关概念串联
## 进阶思考题
"""


class ReadingAgent(BaseAgent):
    """生成拓展阅读材料。"""

    name = "reading"

    def __init__(self, llm: SparkLLMClient) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        profile = state.get("profile", {})
        context = state.get("retrieved_context", [])
        prompt = self._build_prompt(knowledge, profile, context)
        try:
            content = await self.llm.chat(prompt, temperature=0.8)
        except LLMError:
            return {}
        return {
            "reading": {
                "type": "reading",
                "content": content,
            }
        }

    def _build_prompt(
        self,
        knowledge: str,
        profile: dict[str, Any],
        context: list[dict[str, Any]],
    ) -> str:
        """构建拓展阅读 Prompt：在掌握基础知识之上做深度延伸。"""
        refs = "\n".join(c.get("content", "") for c in context)
        ref_block = f"参考资料：\n{refs}\n\n" if refs else ""
        return (
            f"你是学习引导专家。为已了解「{knowledge}」基础的学生整理拓展阅读材料，"
            f"内容要有前沿性、启发性，引导深入探索，不要重复基础讲解。\n"
            f"学生画像：{profile}\n"
            f"{ref_block}"
            f"请按如下结构输出 Markdown：\n{READING_TEMPLATE}"
        )
