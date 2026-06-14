"""讯飞星火大模型客户端封装。

提供同步/流式对话、文本向量化接口，内置重试与限流退避。
所有 Agent 通过本客户端访问 LLM，便于统一管理鉴权、超时与降级。

注意：当前为框架骨架，``_call_api`` 内为占位实现。接入真实讯飞 API 时，
按 §5.2.1 替换鉴权与请求逻辑即可，对上层 Agent 透明。
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM 调用异常。"""


class SparkLLMClient:
    """讯飞星火大模型客户端。

    Args:
        app_id: 应用 ID
        api_key: API Key
        api_secret: API Secret
        max_retries: 失败重试次数（§4.5.1 规定 3 次）
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        self.app_id = app_id or settings.spark_app_id
        self.api_key = api_key or settings.spark_api_key
        self.api_secret = api_secret or settings.spark_api_secret
        self.max_retries = max_retries

    async def chat(self, prompt: str, *, temperature: float = 0.7) -> str:
        """同步对话：返回完整回复文本。

        失败自动重试 ``max_retries`` 次，指数退避。全部失败抛 ``LLMError``。
        """
        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await self._call_api(prompt, temperature=temperature)
            except Exception as exc:  # noqa: BLE001 - 统一兜底重试
                last_err = exc
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "LLM 调用失败 (第 %d/%d 次)，%.0fs 后重试: %s",
                    attempt, self.max_retries, wait, exc,
                )
                await asyncio.sleep(wait)
        raise LLMError(f"LLM 调用在 {self.max_retries} 次重试后仍失败") from last_err

    async def chat_stream(self, prompt: str, *, temperature: float = 0.7) -> AsyncIterator[str]:
        """流式对话：逐 token 产出，供 SSE 接口转发（§4.4.2）。"""
        text = await self.chat(prompt, temperature=temperature)
        for token in text:
            yield token
            await asyncio.sleep(0)

    async def embed(self, text: str) -> list[float]:
        """文本向量化：返回 1024 维向量（对齐 BGE-large-zh，§6.3）。"""
        # 占位：接入 /v1/embeddings 后替换
        raise NotImplementedError("embed() 待接入讯飞向量化 API")

    async def classify_intent(self, user_input: str) -> str:
        """意图分类：供 Orchestrator 路由（§4.2.1）。

        返回意图标签之一：build_profile / generate_resource / plan_path / assess / chat
        """
        raise NotImplementedError("classify_intent() 待接入 LLM")

    async def _call_api(self, prompt: str, *, temperature: float) -> str:
        """实际 HTTP 调用占位。接入真实 API 时在此实现。"""
        raise NotImplementedError(
            "SparkLLMClient._call_api 为骨架占位，需按 §5.2.1 接入讯飞星火 API"
        )
