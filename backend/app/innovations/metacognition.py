"""元认知能力培养（IN-08, P1）。

显性训练学生的"学会学习"能力：学习前预测掌握度 -> 学习后对比实际得分 ->
反馈校准度，长期提升自我评估准确性。

设计依据：设计说明书 §3.7。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def ewma_update(old: float, observed: float, alpha: float = 0.3) -> float:
    """EWMA 指数加权移动平均更新（§7.3.1）。

    V_new = α · V_observed + (1 - α) · V_old

    用于数值型画像维度（如知识基础、元认知校准度）的动态平滑更新：
    ``alpha`` 越大越偏向最新观测，越小越依赖历史。结果钳制到 [0, 1]。
    """
    value = alpha * observed + (1 - alpha) * old
    return max(0.0, min(1.0, value))


class MetacognitionTrainer:
    """元认知能力培养器。

    依赖数据访问对象 ``db``，需提供：

    - ``save_prediction(student_id, topic, prediction)``
    - ``get_prediction(student_id, topic) -> int | None``
    """

    # 校准度（预测与实际的绝对差）阈值
    _POOR_CALIBRATION = 0.3
    _OK_CALIBRATION = 0.15

    def __init__(self, db) -> None:
        self.db = db

    def pre_learning(self, student_id: str, topic: str) -> dict:
        """学习前：生成预测提示。"""
        return {
            "prompt": f"你觉得你能掌握『{topic}』吗？(1-10 分)",
            "topic": topic,
            "student_id": student_id,
        }

    def record_prediction(self, student_id: str, topic: str, prediction: int) -> None:
        """记录预测分数（1-10）。"""
        prediction = max(1, min(10, prediction))
        self.db.save_prediction(student_id, topic, prediction)

    def post_learning(self, student_id: str, topic: str, actual_score: float) -> dict:
        """学习后：对比预测与实际，返回校准反馈。"""
        prediction = self.db.get_prediction(student_id, topic)
        if prediction is None:
            return {"feedback": "未记录预测，无法评估元认知校准度。"}

        prediction_normalized = prediction / 10.0
        calibration = abs(prediction_normalized - actual_score)

        if calibration > self._POOR_CALIBRATION:
            feedback = "你的自我评估和实际结果差距较大，建议更客观地评估自己的理解。"
        elif calibration > self._OK_CALIBRATION:
            feedback = "你的自我评估基本准确，继续保持。"
        else:
            feedback = "你的自我评估非常准确，这是高效学习的重要能力！"

        return {
            "prediction": prediction,
            "actual": actual_score,
            "calibration": round(calibration, 3),
            "feedback": feedback,
        }
