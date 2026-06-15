"""PostgreSQL 真实仓储实现（替换 `_PlaceholderRepo`）。

基于 SQLAlchemy 2.0 异步会话，实现画像/学习记录/资源/路径/遗忘曲线/元认知的 CRUD。
图谱/向量操作仍为占位（需 Neo4j/Milvus 接入）。

设计依据：§6.1.1 核心表结构 + 附录 A 建表脚本。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    User,
    StudentProfile,
    LearningRecord,
    GeneratedResource,
    LearningPath,
    ForgettingCurve,
    ReviewSchedule,
    MetacognitionPrediction,
)

logger = logging.getLogger(__name__)


class PostgresRepository:
    """PostgreSQL 真实仓储。

    依赖注入 ``AsyncSession``（FastAPI 依赖 ``get_session`` 产出）。
    所有方法均为异步，遵循「读不锁、写事务」原则。
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- 用户与画像 ---------------------------------------------------------

    async def get_or_create_user(self, student_id: str, username: str = "", email: str = "") -> User:
        """获取或创建用户（按 student_id 查 username 字段，缺省用 student_id 填充）。"""
        stmt = select(User).where(User.username == student_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                username=student_id,
                email=email or f"{student_id}@example.com",
                password_hash="placeholder",  # 真实注册时替换
                role="student",
            )
            self.session.add(user)
            await self.session.flush()
        return user

    async def get_profile(self, student_id: str) -> Dict[str, Any]:
        """加载学生画像（6 维度），返回 dict。无记录返回空 dict。"""
        stmt = select(StudentProfile).where(StudentProfile.student_id == student_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            return {}
        return {
            "major": profile.major,
            "grade": profile.grade,
            "learning_goal": profile.learning_goal,
            "knowledge_base": profile.knowledge_base,
            "learning_style": profile.learning_style,
            "motivation": profile.motivation,
            "motivation_strength": profile.motivation_strength,
            "metacognition": profile.metacognition,
            "scaffold_level": profile.scaffold_level,
            "version": profile.version,
        }

    async def get_or_create_profile(self, student_id: str) -> Dict[str, Any]:
        """获取或初始化画像（Profile Agent 调用）。"""
        user = await self.get_or_create_user(student_id)
        profile = await self.get_profile(user.id)
        if not profile:
            profile_obj = StudentProfile(student_id=user.id, scaffold_level="medium", version=1)
            self.session.add(profile_obj)
            await self.session.flush()
            return self._profile_to_dict(profile_obj)
        return profile

    async def update_profile(self, student_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新画像维度（支持部分更新），返回更新后画像。"""
        user = await self.get_or_create_user(student_id)
        stmt = select(StudentProfile).where(StudentProfile.student_id == user.id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = StudentProfile(student_id=user.id, scaffold_level="medium", version=1)
            self.session.add(profile)
            await self.session.flush()

        for key, value in updates.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        profile.version = (profile.version or 1) + 1
        profile.updated_at = datetime.utcnow()
        await self.session.flush()
        return self._profile_to_dict(profile)

    @staticmethod
    def _profile_to_dict(profile: StudentProfile) -> Dict[str, Any]:
        return {
            "major": profile.major,
            "grade": profile.grade,
            "learning_goal": profile.learning_goal,
            "knowledge_base": profile.knowledge_base,
            "learning_style": profile.learning_style,
            "motivation": profile.motivation,
            "motivation_strength": profile.motivation_strength,
            "metacognition": profile.metacognition,
            "scaffold_level": profile.scaffold_level,
            "version": profile.version,
        }

    # --- 学习记录 -----------------------------------------------------------

    async def save_learning_record(
        self,
        student_id: str,
        knowledge_id: int,
        action_type: str,
        score: Optional[float] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> None:
        """记录学习行为（learn/review/test）。"""
        user = await self.get_or_create_user(student_id)
        record = LearningRecord(
            student_id=user.id,
            knowledge_id=knowledge_id,
            action_type=action_type,
            score=score,
            time_spent_seconds=time_spent_seconds,
        )
        self.session.add(record)

    async def get_learning_records(
        self, student_id: str, knowledge_id: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询学习记录（按时间倒序）。"""
        user = await self.get_or_create_user(student_id)
        stmt = select(LearningRecord).where(LearningRecord.student_id == user.id)
        if knowledge_id is not None:
            stmt = stmt.where(LearningRecord.knowledge_id == knowledge_id)
        stmt = stmt.order_by(LearningRecord.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "id": r.id,
                "knowledge_id": r.knowledge_id,
                "action_type": r.action_type,
                "score": r.score,
                "time_spent_seconds": r.time_spent_seconds,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]

    # --- 生成资源 -----------------------------------------------------------

    async def save_resource(
        self,
        student_id: str,
        knowledge_id: Optional[int],
        resource_type: str,
        content: Dict[str, Any],
        scaffold_level: Optional[str] = None,
        quality_score: Optional[float] = None,
        review_status: str = "pending",
    ) -> int:
        """保存生成的资源，返回资源 ID。"""
        user = await self.get_or_create_user(student_id)
        resource = GeneratedResource(
            student_id=user.id,
            knowledge_id=knowledge_id,
            resource_type=resource_type,
            content=content,
            scaffold_level=scaffold_level,
            quality_score=quality_score,
            review_status=review_status,
        )
        self.session.add(resource)
        await self.session.flush()
        return resource.id

    async def get_resources(
        self, student_id: str, resource_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """查询学生已生成的资源列表。"""
        user = await self.get_or_create_user(student_id)
        stmt = select(GeneratedResource).where(GeneratedResource.student_id == user.id)
        if resource_type is not None:
            stmt = stmt.where(GeneratedResource.resource_type == resource_type)
        stmt = stmt.order_by(GeneratedResource.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        resources = result.scalars().all()
        return [
            {
                "id": r.id,
                "resource_type": r.resource_type,
                "content": r.content,
                "scaffold_level": r.scaffold_level,
                "quality_score": r.quality_score,
                "review_status": r.review_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in resources
        ]

    # --- 学习路径 -----------------------------------------------------------

    async def save_path(
        self,
        student_id: str,
        path_data: Dict[str, Any],
        current_node_id: Optional[int] = None,
        status: str = "active",
    ) -> int:
        """保存学习路径（DAG 节点序列），返回路径 ID。"""
        user = await self.get_or_create_user(student_id)
        path = LearningPath(
            student_id=user.id,
            path_data=path_data,
            current_node_id=current_node_id,
            status=status,
        )
        self.session.add(path)
        await self.session.flush()
        return path.id

    async def get_active_path(self, student_id: str) -> Optional[Dict[str, Any]]:
        """获取学生当前活跃的学习路径。"""
        user = await self.get_or_create_user(student_id)
        stmt = (
            select(LearningPath)
            .where(and_(LearningPath.student_id == user.id, LearningPath.status == "active"))
            .order_by(LearningPath.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        path = result.scalar_one_or_none()
        if path is None:
            return None
        return {
            "id": path.id,
            "path_data": path.path_data,
            "current_node_id": path.current_node_id,
            "status": path.status,
            "created_at": path.created_at.isoformat() if path.created_at else None,
        }

    # --- 遗忘曲线 -----------------------------------------------------------

    async def save_forgetting_curve(
        self,
        student_id: str,
        knowledge_id: int,
        a: float,
        b: float,
        optimal_interval: float,
        data_points: int,
        r_squared: float,
    ) -> None:
        """保存或更新遗忘曲线参数（UPSERT）。"""
        user = await self.get_or_create_user(student_id)
        stmt = select(ForgettingCurve).where(
            and_(
                ForgettingCurve.student_id == user.id,
                ForgettingCurve.knowledge_id == knowledge_id,
            )
        )
        result = await self.session.execute(stmt)
        curve = result.scalar_one_or_none()
        if curve is None:
            curve = ForgettingCurve(
                student_id=user.id,
                knowledge_id=knowledge_id,
                a=a,
                b=b,
                optimal_interval=optimal_interval,
                data_points=data_points,
                r_squared=r_squared,
            )
            self.session.add(curve)
        else:
            curve.a = a
            curve.b = b
            curve.optimal_interval = optimal_interval
            curve.data_points = data_points
            curve.r_squared = r_squared
            curve.updated_at = datetime.utcnow()

    async def get_forgetting_curve(self, student_id: str, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """获取遗忘曲线参数。"""
        user = await self.get_or_create_user(student_id)
        stmt = select(ForgettingCurve).where(
            and_(
                ForgettingCurve.student_id == user.id,
                ForgettingCurve.knowledge_id == knowledge_id,
            )
        )
        result = await self.session.execute(stmt)
        curve = result.scalar_one_or_none()
        if curve is None:
            return None
        return {
            "a": curve.a,
            "b": curve.b,
            "optimal_interval": curve.optimal_interval,
            "data_points": curve.data_points,
            "r_squared": curve.r_squared,
        }

    # --- 复习计划 -----------------------------------------------------------

    async def save_review_schedule(
        self,
        student_id: str,
        knowledge_id: int,
        scheduled_time: datetime,
        predicted_score: Optional[float] = None,
    ) -> int:
        """保存复习计划，返回计划 ID。"""
        user = await self.get_or_create_user(student_id)
        schedule = ReviewSchedule(
            student_id=user.id,
            knowledge_id=knowledge_id,
            scheduled_time=scheduled_time,
            predicted_score=predicted_score,
        )
        self.session.add(schedule)
        await self.session.flush()
        return schedule.id

    async def get_pending_reviews(self, student_id: str) -> List[Dict[str, Any]]:
        """获取待完成的复习计划（按时间升序）。"""
        user = await self.get_or_create_user(student_id)
        stmt = (
            select(ReviewSchedule)
            .where(and_(ReviewSchedule.student_id == user.id, ReviewSchedule.status == "pending"))
            .order_by(ReviewSchedule.scheduled_time.asc())
        )
        result = await self.session.execute(stmt)
        schedules = result.scalars().all()
        return [
            {
                "id": s.id,
                "knowledge_id": s.knowledge_id,
                "scheduled_time": s.scheduled_time.isoformat() if s.scheduled_time else None,
                "predicted_score": s.predicted_score,
            }
            for s in schedules
        ]

    # --- 元认知预测 ---------------------------------------------------------

    async def save_prediction(self, student_id: str, topic: str, prediction: int) -> None:
        """记录学习前预测（MetacognitionTrainer 调用）。"""
        user = await self.get_or_create_user(student_id)
        pred = MetacognitionPrediction(
            student_id=user.id,
            topic=topic,
            prediction=prediction,
        )
        self.session.add(pred)

    async def get_prediction(self, student_id: str, topic: str) -> Optional[int]:
        """获取最近一次预测（MetacognitionTrainer 调用）。"""
        user = await self.get_or_create_user(student_id)
        stmt = (
            select(MetacognitionPrediction)
            .where(and_(MetacognitionPrediction.student_id == user.id, MetacognitionPrediction.topic == topic))
            .order_by(MetacognitionPrediction.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        pred = result.scalar_one_or_none()
        return pred.prediction if pred else None

    # --- 图谱/向量占位（需 Neo4j/Milvus 接入）-------------------------------

    async def get_subgraph(self, target: str, max_depth: int = 5) -> Dict[str, Dict[str, float]]:
        """从知识图谱获取目标子图（DAG）。接 Neo4j 后替换。"""
        return {target: {}}

    def prerequisite_chain(self, target: str) -> List[Dict[str, Any]]:
        """前置知识链（供 ExplainableRecommender 同步查询）。接 Neo4j 后替换。"""
        return []

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """向量检索（接 Milvus 后替换）。"""
        return []

    async def query_entities(self, entities: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """图谱实体查询（接 Neo4j 后替换）。"""
        return []

    # --- 评估维度计算（占位，需真实行为数据）---------------------------------

    async def compute_assessment_dimensions(self, student_id: str, dimensions: List[str]) -> Dict[str, float]:
        """计算 10 维度评估得分（Assessment Agent 调用）。

        当前返回中性值 0.5；接入真实学习记录后按权重公式计算。
        """
        return {dim: 0.5 for dim in dimensions}
