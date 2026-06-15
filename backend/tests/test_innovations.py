"""核心创新算法单元测试。

验证 3 个 P0 创新模块的纯算法逻辑，不依赖外部服务。
"""

import pytest
from datetime import datetime, timedelta

from app.innovations.forgetting_curve import ForgettingCurveModel, ReviewRecord
from app.innovations.scaffold_generator import ScaffoldGenerator, ScaffoldLevel
from app.innovations.explainable_recommender import ExplainableRecommender


class TestForgettingCurve:
    """遗忘曲线拟合测试（IN-04）。"""

    def test_fit_with_sufficient_data(self):
        """数据点充足时应成功拟合。"""
        model = ForgettingCurveModel()
        records = [
            ReviewRecord("k1", 1, 0.85, "test"),
            ReviewRecord("k1", 3, 0.70, "test"),
            ReviewRecord("k1", 7, 0.50, "test"),
            ReviewRecord("k1", 14, 0.35, "test"),
        ]
        curve = model.fit(records)
        assert curve.a > 0.5
        assert curve.b > 0.01
        assert curve.optimal_interval > 0
        assert curve.data_points == 4
        assert curve.r_squared > 0.5  # R² 应大于 0.5

    def test_fit_with_insufficient_data(self):
        """数据点不足时应返回默认曲线。"""
        model = ForgettingCurveModel()
        records = [ReviewRecord("k1", 1, 0.85, "test")]
        curve = model.fit(records)
        assert curve.a == 0.95  # 默认值
        assert curve.b == 0.15
        assert curve.data_points == 0

    def test_predict_score(self):
        """预测分数应在 0-1 之间。"""
        model = ForgettingCurveModel()
        records = [
            ReviewRecord("k1", 1, 0.85, "test"),
            ReviewRecord("k1", 3, 0.70, "test"),
            ReviewRecord("k1", 7, 0.50, "test"),
        ]
        curve = model.fit(records)
        score = model.predict_score(curve, 5)
        assert 0 <= score <= 1

    def test_review_schedule(self):
        """复习计划应返回未来时间。"""
        model = ForgettingCurveModel()
        records = [
            ReviewRecord("k1", 1, 0.85, "test"),
            ReviewRecord("k1", 3, 0.70, "test"),
            ReviewRecord("k1", 7, 0.50, "test"),
        ]
        curve = model.fit(records)
        last_review = datetime.now()
        schedule = model.get_review_schedule(curve, last_review)
        assert schedule.next_review > last_review
        assert schedule.optimal_interval > 0


class TestScaffoldGenerator:
    """脚手架分级测试（IN-07）。"""

    def test_determine_level_beginner(self):
        """掌握度 < 50% 应为高支持。"""
        gen = ScaffoldGenerator()
        assert gen.determine_level(0.3) == ScaffoldLevel.HIGH

    def test_determine_level_intermediate(self):
        """掌握度 50-80% 应为中支持。"""
        gen = ScaffoldGenerator()
        assert gen.determine_level(0.65) == ScaffoldLevel.MEDIUM

    def test_determine_level_advanced(self):
        """掌握度 > 80% 应为低支持。"""
        gen = ScaffoldGenerator()
        assert gen.determine_level(0.9) == ScaffoldLevel.LOW

    def test_generate_high_support(self):
        """高支持脚手架应包含步骤和提示。"""
        gen = ScaffoldGenerator()
        content = gen.generate("注意力机制", 0.3)
        assert content.level == ScaffoldLevel.HIGH
        assert content.steps is not None
        assert len(content.steps) >= 3
        assert content.hints is not None

    def test_generate_low_support(self):
        """低支持脚手架应包含挑战性任务。"""
        gen = ScaffoldGenerator()
        content = gen.generate("注意力机制", 0.9)
        assert content.level == ScaffoldLevel.LOW
        assert content.challenge is not None

    def test_adjust_level_upgrade(self):
        """表现优秀时应升级脚手架。"""
        gen = ScaffoldGenerator()
        new_level = gen.adjust_level(ScaffoldLevel.MEDIUM, 0.85, "improving")
        assert new_level == ScaffoldLevel.LOW

    def test_adjust_level_downgrade(self):
        """表现差时应降级脚手架。"""
        gen = ScaffoldGenerator()
        new_level = gen.adjust_level(ScaffoldLevel.MEDIUM, 0.4, "declining")
        assert new_level == ScaffoldLevel.HIGH


class TestExplainableRecommender:
    """可解释推荐测试（IN-03）。"""

    def test_recommend_with_weak_prerequisite(self):
        """存在薄弱前置知识时应推荐先学前置。"""

        class MockRepo:
            def prerequisite_chain(self, target):
                return [
                    {"name": "线性代数", "difficulty": 3, "category": "math"},
                    {"name": "概率论", "difficulty": 4, "category": "math"},
                ]

        recommender = ExplainableRecommender(MockRepo())
        profile = {"线性代数": 0.85, "概率论": 0.45}
        result = recommender.recommend_with_explanation("s1", "Transformer", profile)
        assert result.recommendation == "概率论"
        assert result.confidence > 0
        assert len(result.explanation) > 10

    def test_recommend_all_mastered(self):
        """所有前置知识已掌握时应推荐直接学习目标。"""

        class MockRepo:
            def prerequisite_chain(self, target):
                return [{"name": "线性代数", "difficulty": 3, "category": "math"}]

        recommender = ExplainableRecommender(MockRepo())
        profile = {"线性代数": 0.9}
        result = recommender.recommend_with_explanation("s1", "Transformer", profile)
        assert result.recommendation == "Transformer"
        assert result.confidence > 0.8

    def test_explain_path_adjustment(self):
        """路径调整应给出理由。"""
        recommender = ExplainableRecommender(None)
        original = ["A", "B", "C"]
        new_path = ["A", "B", "D", "C"]
        assessment = {"D": {"score": 0.55}}
        explanation = recommender.explain_path_adjustment(original, new_path, assessment)
        assert "D" in explanation
        assert "55%" in explanation
