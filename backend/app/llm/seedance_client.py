"""SeeDance 多模态视频生成客户端（§5.2.2）。

视频生成耗时 3-10 分钟，采用异步提交 + 轮询状态模式（TC-002）。
鉴权：API Key 作 Bearer token（与讯飞星火 HTTP 版一致）。

当前为框架骨架，实际 HTTP 调用为占位实现。接入真实 API 时替换
``_call_api`` 内的请求逻辑即可，对上层 Video Agent 透明。
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VideoTask:
    """视频生成任务状态。"""

    task_id: str
    status: str  # processing / completed / failed
    progress: int = 0  # 0-100
    video_url: Optional[str] = None
    error_message: Optional[str] = None


class SeeDanceClient:
    """SeeDance 视频生成客户端。

    Args:
        api_key: 控制台 API Key；缺省读取配置 ``seedance_api_key``。
        base_url: 服务根地址。
        max_retries: 失败重试次数。
        timeout: 单次请求超时（秒）。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or settings.seedance_api_key
        self.base_url = (base_url or settings.seedance_base_url).rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

    # --- 公共接口 -----------------------------------------------------------

    async def submit_task(
        self,
        *,
        script: str,
        style: str = "educational",
        duration: int = 90,
    ) -> dict[str, Any]:
        """提交视频生成任务，返回 task_id（异步，立即返回）。

        失败自动重试 ``max_retries`` 次，指数退避。全部失败抛 ``VideoError``。
        """
        payload = {
            "script": script,
            "style": style,
            "duration": duration,
        }
        data = await self._request("/v1/video/generate", payload)
        try:
            return {"task_id": data["task_id"], "status": "processing"}
        except KeyError as exc:
            raise VideoError(f"SeeDance 返回结构异常：{data}") from exc

    async def get_status(self, task_id: str) -> VideoTask:
        """查询任务状态（§5.2.2 /v1/video/status，30 次/分钟）。"""
        data = await self._request("/v1/video/status", {"task_id": task_id})
        return VideoTask(
            task_id=task_id,
            status=data.get("status", "unknown"),
            progress=data.get("progress", 0),
            video_url=data.get("video_url"),
            error_message=data.get("error_message"),
        )

    async def wait_for_completion(
        self, task_id: str, poll_interval: float = 10.0, max_wait: float = 600.0
    ) -> VideoTask:
        """轮询等待任务完成（默认最多等 10 分钟，每 10 秒查一次）。"""
        elapsed = 0.0
        while elapsed < max_wait:
            task = await self.get_status(task_id)
            if task.status in ("completed", "failed"):
                return task
            logger.info("视频任务 %s 进度 %d%%，继续等待...", task_id, task.progress)
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return VideoTask(
            task_id=task_id, status="timeout", progress=0, error_message="等待超时"
        )

    # --- 内部实现 -----------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise VideoError("未配置 seedance_api_key，无法调用 SeeDance API")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """执行 HTTP 调用，失败指数退避重试。"""
        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        self.base_url + path, headers=self._headers(), json=payload
                    )
                    resp.raise_for_status()
                    return resp.json()
            except Exception as exc:  # noqa: BLE001 - 统一兜底重试
                last_err = exc
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "SeeDance 调用失败 (第 %d/%d 次)，%.0fs 后重试：%s",
                    attempt, self.max_retries, wait, exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(wait)
        raise VideoError(f"SeeDance 调用在 {self.max_retries} 次重试后仍失败") from last_err


class VideoError(Exception):
    """SeeDance 调用异常。"""
