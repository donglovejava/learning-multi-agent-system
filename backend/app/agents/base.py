"""Agent 基类与共享状态定义。

所有 Agent 继承 ``BaseAgent``，遵循统一生命周期（§4.1.2）：
初始化 → 等待任务 → 执行 → 返回结果。单一职责、松耦合（§4.1.1）。
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, TypedDict

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """LangGraph 共享状态（在 11 个 Agent 间流转，§4.4.1）。

    每个 Agent 读取所需字段、写回自己的产出，避免直接互相调用。
    """

    # 输入
    student_id: str
    user_input: str
    intent: str
    knowledge_point: str
    resource_types: list[str]
    scaffold_level: str

    # 上下文
    profile: dict[str, Any]
    retrieved_context: list[dict[str, Any]]

    # 产出（各资源 Agent 写回）
    document: Optional[dict[str, Any]]
    quiz: Optional[dict[str, Any]]
    mindmap: Optional[dict[str, Any]]
    video: Optional[dict[str, Any]]
    code: Optional[dict[str, Any]]
    path: Optional[dict[str, Any]]
    assessment: Optional[dict[str, Any]]

    # 审核与解释
    review_result: Optional[dict[str, Any]]
    explanation: Optional[str]

    # 元信息
    errors: list[str]
    timings: dict[str, float]


class BaseAgent(ABC):
    """Agent 抽象基类。

    子类实现 ``run``，返回对 ``AgentState`` 的增量更新（dict）。
    基类负责计时、异常隔离（单 Agent 故障不影响整体，§4.5.2）。
    """

    name: str = "base"

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            update = await self.run(state)
        except Exception as exc:  # noqa: BLE001 - 故障隔离，记录后降级
            logger.exception("Agent %s 执行失败", self.name)
            errors = list(state.get("errors", []))
            errors.append(f"{self.name}: {exc}")
            return {"errors": errors}
        finally:
            elapsed = time.perf_counter() - start
            logger.info("Agent %s 耗时 %.3fs", self.name, elapsed)

        timings = dict(state.get("timings", {}))
        timings[self.name] = round(time.perf_counter() - start, 3)
        update.setdefault("timings", timings)
        return update

    @abstractmethod
    async def run(self, state: AgentState) -> dict[str, Any]:
        """执行 Agent 逻辑，返回 state 增量更新。"""
        raise NotImplementedError
