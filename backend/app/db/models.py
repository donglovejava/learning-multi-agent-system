"""SQLAlchemy ORM 模型，对应 §6.1.1 核心表结构与附录 A。

仅建模骨架阶段需要的核心表；JSONB 字段承载半结构化产出（资源、路径）。
枚举值（角色/资源类型/状态）以约束在应用层校验，DB 侧用 CHECK/默认值兜底。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    """用户表（学生/教师/管理员），§6.1.1。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False)

    __table_args__ = (
        CheckConstraint("role IN ('student','teacher','admin')", name="ck_users_role"),
    )


class StudentProfile(Base):
    """6 维度学习画像，§4.2.2 / §6.1.1。"""

    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    major: Mapped[str | None] = mapped_column(String(100))
    grade: Mapped[str | None] = mapped_column(String(20))
    learning_goal: Mapped[str | None] = mapped_column(String(50))
    knowledge_base: Mapped[float | None] = mapped_column(Float)
    learning_style: Mapped[str | None] = mapped_column(String(20))
    motivation: Mapped[str | None] = mapped_column(String(20))
    motivation_strength: Mapped[float | None] = mapped_column(Float)
    metacognition: Mapped[float | None] = mapped_column(Float)
    scaffold_level: Mapped[str] = mapped_column(String(10), default="medium")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="profile")

    __table_args__ = (
        CheckConstraint(
            "knowledge_base >= 0 AND knowledge_base <= 1", name="ck_profile_kb_range"
        ),
    )


class KnowledgeNode(Base):
    """知识图谱节点（PostgreSQL 侧镜像，图关系存 Neo4j），§6.1.1。"""

    __tablename__ = "knowledge_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    course_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("difficulty >= 1 AND difficulty <= 5", name="ck_node_difficulty"),
    )


class LearningRecord(Base):
    """学习/复习/测试行为记录，遗忘曲线拟合数据来源，§3.2.4 / §6.1.1。"""

    __tablename__ = "learning_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    knowledge_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 1", name="ck_record_score_range"),
    )


class ForgettingCurve(Base):
    """个性化遗忘曲线参数（IN-04），§3.2.4。"""

    __tablename__ = "forgetting_curves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    knowledge_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=False
    )
    a: Mapped[float] = mapped_column(Float, nullable=False)
    b: Mapped[float] = mapped_column(Float, nullable=False)
    optimal_interval: Mapped[float] = mapped_column(Float, nullable=False)
    data_points: Mapped[int] = mapped_column(Integer, default=0)
    r_squared: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("student_id", "knowledge_id", name="uq_curve_student_knowledge"),
    )


class GeneratedResource(Base):
    """多智能体生成的资源（文档/题目/导图/视频/代码），§6.1.1。"""

    __tablename__ = "generated_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    knowledge_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_nodes.id"))
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scaffold_level: Mapped[str | None] = mapped_column(String(10))
    quality_score: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LearningPath(Base):
    """学习路径（DAG 节点序列存 JSONB），§6.1.1。"""

    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    path_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    current_node_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ReviewSchedule(Base):
    """复习计划（遗忘曲线驱动），§3.2.4 / §6.1.1。"""

    __tablename__ = "review_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    knowledge_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=False
    )
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    predicted_score: Mapped[float | None] = mapped_column(Float)
    actual_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MetacognitionPrediction(Base):
    """元认知预测记录（IN-08），§3.7。"""

    __tablename__ = "metacognition_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    prediction: Mapped[int] = mapped_column(Integer)
    actual_score: Mapped[float | None] = mapped_column(Float)
    calibration: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("prediction >= 1 AND prediction <= 10", name="ck_pred_range"),
    )
