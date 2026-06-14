"""SeeDance 多模态视频生成客户端封装（§5.2.2）。

视频生成耗时 3-10 分钟，采用异步提交 + 轮询状态模式（TC-002）。
Video Agent 通过本客户端提交任务并追踪进度，配合 Celery 异步执行。

当前为框架骨架，实际 HTTP 调用为占位实现。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VideoTask:
    """视频生成任务状态。"""

    task_id: str
    status: str  # processing / completed / failed
    progress: int = 0  # 0-100
    video_url: Optional[str] = None


class SeeDanceClient:
    """SeeDance 视频生成客户端。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or settings.seedance_api_key
        self.max_retries = max_retries

    async def submit_task(
        self,
        *,
        script: str,
        style: str = "educational",
        duration: int = 90,
    ) -> str:
        """提交视频生成任务，返回 task_id（异步，立即返回）。"""
        raise NotImplementedError(
            "SeeDanceClient.submit_task 为骨架占位，需按 §5.2.2 接入 /v1/video/generate"
        )

    async def get_status(self, task_id: str) -> VideoTask:
        """查询任务状态（§5.2.2 /v1/video/status，30 次/分钟）。"""
        raise NotImplementedError(
            "SeeDanceClient.get_status 为骨架占位，需按 §5.2.2 接入 /v1/video/status"
        )
