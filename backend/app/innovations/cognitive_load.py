"""认知负荷动态调节（IN-05, P1）。

通过答题速度、错误率、提示请求次数等交互行为，实时估算学生的认知负荷，
并据此动态调整内容难度，保持"难度≈能力"的心流状态。

设计依据：设计说明书 §3.6。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class CognitiveLoadEstimator:
    """认知负荷估算器。

    认知负荷公式（0-1）::

        load = 0.4 * 错误率 + 0.3 * 归一化响应时间 + 0.3 * 归一化提示次数

    难度调整规则：load > 0.7 降难度，load < 0.3 升难度。
    """

    # 归一化基准：响应时间上限 300 秒，提示次数上限 5 次
    _MAX_RESPONSE_TIME = 300.0
    _MAX_HINT_COUNT = 5.0

    _HIGH_LOAD = 0.7
    _LOW_LOAD = 0.3

    def estimate(self, recent_actions: list[dict]) -> float:
        """通过行为数据估算认知负荷。

        Args:
            recent_actions: 近期行为列表，每项含
                response_time(秒) / is_error(bool) / hint_requests(int)。

        Returns:
            认知负荷，范围 [0, 1]。无数据时返回中性值 0.5。
        """
        if not recent_actions:
            return 0.5

        n = len(recent_actions)
        avg_time = sum(a["response_time"] for a in recent_actions) / n
        error_rate = sum(1 for a in recent_actions if a["is_error"]) / n
        hint_count = sum(a["hint_requests"] for a in recent_actions) / n

        load = (
            0.4 * min(error_rate, 1.0)
            + 0.3 * min(avg_time / self._MAX_RESPONSE_TIME, 1.0)
            + 0.3 * min(hint_count / self._MAX_HINT_COUNT, 1.0)
        )
        return max(0.0, min(1.0, load))

    def adjust_difficulty(self, load: float, current_difficulty: int) -> int:
        """根据认知负荷调整难度（1-5 级）。"""
        if load > self._HIGH_LOAD:
            new = max(current_difficulty - 1, 1)
        elif load < self._LOW_LOAD:
            new = min(current_difficulty + 1, 5)
        else:
            new = current_difficulty
        if new != current_difficulty:
            logger.info(
                "认知负荷 %.2f，难度 %d -> %d", load, current_difficulty, new
            )
        return new
