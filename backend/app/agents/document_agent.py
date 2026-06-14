"""Document Agent（文档生成）。

RAG 检索 + 脚手架级别 → Markdown 讲解文档（§4.2.3）。
生成时间目标 ≤10s（PM-006），内容经 Review Agent 审核。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.innovations.scaffold_generator import ScaffoldGenerator
from app.llm.spark_client import SparkLLMClient

#: 讲解文档结构模板（§4.2.3）
DOC_TEMPLATE = """# {knowledge}

## 概述
## 核心概念
## 原理详解
## 示例说明
## 常见误区
## 知识链接
## 小结与思考题
"""


class DocumentAgent(BaseAgent):
    """生成个性化讲解文档。"""

    name = "document"

    def __init__(self, llm: SparkLLMClient, scaffold: ScaffoldGenerator | None = None) -> None:
        self.llm = llm
        self.scaffold = scaffold

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        profile = state.get("profile", {})
        scaffold_level = state.get("scaffold_level", "medium")
        context = state.get("retrieved_context", [])

        prompt = self._build_prompt(knowledge, context, profile, scaffold_level)
        content = await self.llm.chat(prompt)
        return {
            "document": {
                "type": "document",
                "content": content,
                "references": context,
                "scaffold_level": scaffold_level,
            }
        }

    def _build_prompt(
        self,
        knowledge: str,
        context: list[dict[str, Any]],
        profile: dict[str, Any],
        scaffold_level: str,
    ) -> str:
        """构建生成 Prompt：注入检索上下文、画像、脚手架级别。"""
        refs = "\n".join(c.get("content", "") for c in context)
        return (
            f"你是教学文档专家。根据以下资料为学生生成讲解文档。\n"
            f"知识点：{knowledge}\n"
            f"脚手架级别：{scaffold_level}（high=详细/medium=适度/low=精简）\n"
            f"学生画像：{profile}\n"
            f"参考资料：\n{refs}\n\n"
            f"请按如下结构输出 Markdown：\n{DOC_TEMPLATE}"
        )
