"""创新二：个性化遗忘曲线（IN-04）。

指数衰减模型 s = a·exp(-b·t) 拟合 + 最优复习时间计算。
对应设计说明书 3.2 节。纯算法实现，持久化由仓库层负责。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import logging

logger = logging.getLogger(__name__)


@dataclass
class ReviewRecord:
    knowledge_id: str
    time_diff_days: float
    score: float
    review_type: str = "test"


@dataclass
class ForgettingCurve:
    a: float
    b: float
    optimal_interval: float
    data_points: int
    r_squared: float


@dataclass
class ReviewSchedule:
    next_review: datetime
    optimal_interval: float
    predicted_score: float
    confidence: float


class ForgettingCurveModel:
    """个性化遗忘曲线模型（无状态算法核心）。"""

    def __init__(self, target_score: float = 0.7, min_data_points: int = 3) -> None:
        self.target_score = target_score
        self.min_data_points = min_data_points

    def fit(self, records: List[ReviewRecord]) -> ForgettingCurve:
        if len(records) < self.min_data_points:
            logger.info("遗忘曲线数据点不足（%d），使用默认曲线", len(records))
            return self.default_curve()
        times = [r.time_diff_days for r in records]
        scores = [r.score for r in records]
        a, b, r2 = self._fit_exponential(times, scores)
        optimal = self._calc_optimal_time(a, b)
        return ForgettingCurve(a, b, optimal, len(records), r2)

    def get_review_schedule(
        self, curve: Optional[ForgettingCurve], last_review_time: datetime
    ) -> ReviewSchedule:
        if curve is None:
            return ReviewSchedule(
                next_review=last_review_time + timedelta(days=1),
                optimal_interval=1.0,
                predicted_score=self.target_score,
                confidence=0.5,
            )
        confidence = min(curve.r_squared * (curve.data_points / 5), 0.95)
        return ReviewSchedule(
            next_review=last_review_time + timedelta(days=curve.optimal_interval),
            optimal_interval=curve.optimal_interval,
            predicted_score=self.target_score,
            confidence=confidence,
        )

    def predict_score(
        self, curve: Optional[ForgettingCurve], days_since_review: float
    ) -> float:
        if curve is None:
            return math.exp(-0.15 * days_since_review)
        predicted = curve.a * math.exp(-curve.b * days_since_review)
        return max(0.0, min(1.0, predicted))

    def _fit_exponential(
        self, times: List[float], scores: List[float]
    ) -> Tuple[float, float, float]:
        """log(s) = log(a) - b·t 线性回归求解。"""
        valid = [(t, s) for t, s in zip(times, scores) if s > 0.01]
        if len(valid) < 2:
            return 1.0, 0.1, 0.0
        n = len(valid)
        log_scores = [math.log(s) for _, s in valid]
        ts = [t for t, _ in valid]
        sum_t, sum_y = sum(ts), sum(log_scores)
        sum_ty = sum(t * y for t, y in zip(ts, log_scores))
        sum_t2 = sum(t * t for t in ts)
        denom = n * sum_t2 - sum_t * sum_t
        if denom == 0:
            return 1.0, 0.1, 0.0
        b_neg = (n * sum_ty - sum_t * sum_y) / denom
        log_a = (sum_y - b_neg * sum_t) / n
        a, b = math.exp(log_a), -b_neg
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in log_scores)
        y_pred = [log_a + b_neg * t for t in ts]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(log_scores, y_pred))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        a = max(0.5, min(1.0, a))
        b = max(0.01, min(1.0, b))
        return a, b, r2

    def _calc_optimal_time(self, a: float, b: float) -> float:
        if b <= 0 or a <= self.target_score:
            return 7.0
        t = -math.log(self.target_score / a) / b
        return max(0.5, min(30.0, t))

    @staticmethod
    def default_curve() -> ForgettingCurve:
        return ForgettingCurve(a=0.95, b=0.15, optimal_interval=3.0, data_points=0, r_squared=0.0)
