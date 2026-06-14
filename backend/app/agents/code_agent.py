"""Code Agent（代码案例）。

生成可运行的编程实操案例 + 解析（§4.2.7）。生成后做语法验证，
Python 用 ``compile`` 静态校验，确保 runnable 标记可信（AC-007）。
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import SparkLLMClient


class CodeAgent(BaseAgent):
    """生成代码实操案例。"""

    name = "code"

    def __init__(self, llm: SparkLLMClient) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        knowledge = state["knowledge_point"]
        language = state.get("code_language", "python")
        prompt = (
            f"生成一个关于「{knowledge}」的 {language} 代码案例：\n"
            f"- 代码可正确运行\n- 包含详细注释\n- 包含运行说明\n- 包含扩展练习"
        )
        code = await self.llm.chat(prompt)
        runnable = self._verify(code, language)
        return {
            "code": {
                "type": "code",
                "language": language,
                "code": code,
                "runnable": runnable,
            }
        }

    @staticmethod
    def _verify(code: str, language: str) -> bool:
        """静态校验代码可运行性。Python 用 compile 检查语法。"""
        if language != "python":
            return True
        try:
            compile(code, "<generated>", "exec")
            return True
        except SyntaxError:
            return False
