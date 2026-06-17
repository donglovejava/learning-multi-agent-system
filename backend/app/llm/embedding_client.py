"""讯飞文本向量化客户端（emb-ddc / embedding 接口）。

讯飞向量化走独立的 HTTP 接口，鉴权方式与星火对话 HTTP 版相同
（APIPassword 作 Bearer），但端点和 model 不同。

接口：POST {base_url}/v1/embeddings
请求体：{"model": "emb", "input": ["文本"]}
响应：{data: [{embedding: [...]}]}

对齐 BGE-large-zh，1024 维（§6.3）。
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBED_PATH = "/v1/embeddings"


class EmbeddingClient:
    """讯飞文本向量化客户端。

    与对话共用 APIPassword（同一应用的 http 服务认证）。
    """

    def __init__(
        self,
        api_password: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "emb",
        timeout: float = 30.0,
    ) -> None:
        self.api_password = api_password or settings.spark_api_password
        self.base_url = (base_url or settings.spark_base_url).rstrip("/")
        self.model = model
        self.timeout = timeout

    async def embed(self, text: str) -> list[float]:
        """单条文本向量化，返回 float 向量。"""
        vectors = await self.embed_batch([text])
        return vectors[0] if vectors else []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化（讯飞单次最多约 16 条）。"""
        if not texts or not self.api_password:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_password}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": texts}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.base_url + EMBED_PATH, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("向量化调用失败：%s", str(exc)[:80])
            return []

        result = []
        for item in data.get("data", []):
            emb = item.get("embedding") or item.get("vector")
            if isinstance(emb, list):
                result.append([float(x) for x in emb])
        return result
