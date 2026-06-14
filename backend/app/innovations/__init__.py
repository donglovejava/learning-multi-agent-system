"""核心创新模块包。

P0 核心创新（必须实现）：
- explainable_recommender: 可解释 AI 决策（IN-03）
- forgetting_curve: 个性化遗忘曲线（IN-04）
- scaffold_generator: 知识脚手架动态生成（IN-07）

P1 重要创新（应该实现）：
- cross_modal_linker: 跨模态知识关联（IN-01）
- group_intelligence: 群体智能优化（IN-02）
- cognitive_load: 认知负荷动态调节（IN-05）
- metacognition: 元认知能力培养（IN-08）
"""

from app.innovations.explainable_recommender import (
    ExplainableRecommender,
    RecommendationResult,
)
from app.innovations.forgetting_curve import (
    ForgettingCurveModel,
    ForgettingCurve,
    ReviewRecord,
    ReviewSchedule,
)
from app.innovations.scaffold_generator import (
    ScaffoldGenerator,
    ScaffoldLevel,
    ScaffoldContent,
)

__all__ = [
    "ExplainableRecommender",
    "RecommendationResult",
    "ForgettingCurveModel",
    "ForgettingCurve",
    "ReviewRecord",
    "ReviewSchedule",
    "ScaffoldGenerator",
    "ScaffoldLevel",
    "ScaffoldContent",
]
