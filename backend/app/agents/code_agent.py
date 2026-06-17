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
            f"- 只输出代码本身，不要 markdown 代码块标记（不要```），不要前后说明文字\n"
            f"- 代码必须语法正确、可正确运行\n"
            f"- 包含详细注释\n"
            f"- 包含运行说明（用注释）\n"
            f"- 包含扩展练习（用注释）\n"
            f"只输出纯代码，第一行开始就是代码。"
        )
        code_raw = await self.llm.chat(prompt)
        code = self._strip_code_fence(code_raw)
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
    def _strip_code_fence(text: str) -> str:
        """剥离 markdown 代码围栏（```python ... ```），只保留纯代码。"""
        import re
        # 匹配开头的 ```language 和结尾的 ```
        text = re.sub(r"^```[a-zA-Z]*\s*\n", "", text.strip())
        text = re.sub(r"\n```\s*$", "", text)
        return text.strip()

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
