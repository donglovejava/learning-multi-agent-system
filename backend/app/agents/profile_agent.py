"""Profile Agent（画像构建）。

职责：6 维度学习画像的对话式构建与动态更新（§4.2.2 / §3.1.1）。

真实数据流：
1. 接收学生每轮对话
2. 调 LLM extract_profile_info 抽取 6 维度信息
3. 对数值型维度做 EWMA 平滑更新（§7.3.1）
4. 持久化到 PostgreSQL（student_profiles 表）
5. 缺哪个维度就由 LLM 生成自然引导问题，补全为止
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.innovations.metacognition import ewma_update
from app.llm.spark_client import SparkLLMClient

#: 6 维度 → 画像字段名映射（对齐 student_profiles 表）
DIMENSION_FIELDS: dict[str, str] = {
    "专业": "major",
    "学习目标": "learning_goal",
    "知识基础": "knowledge_base",
    "学习风格": "learning_style",
    "学习动机": "motivation",
    "元认知": "metacognition",
}

#: 数值型维度（做 EWMA 平滑更新），其余为文本直接覆盖
NUMERIC_DIMENSIONS = {"knowledge_base", "metacognition"}


class ProfileAgent(BaseAgent):
    """构建并维护学生 6 维度画像。"""

    name = "profile"

    def __init__(self, llm: SparkLLMClient, repo: Any = None) -> None:
        self.llm = llm
        self.repo = repo

    async def run(self, state: AgentState) -> dict[str, Any]:
        """资源生成流程中仅负责加载画像供下游使用。"""
        student_id = state["student_id"]
        profile = await self._load_profile(student_id)
        return {"profile": profile}

    async def process_reply(
        self, student_id: str, user_message: str, history: list | None = None
    ) -> dict[str, Any]:
        """对话式画像构建单轮处理（§4.2.2）。

        真实流程：LLM 抽取 → EWMA 合并 → 持久化 → 判断是否齐全 → 生成下一问。
        返回 {done, question, profile, summary, completion}。
        """
        history = history or []

        # 1. LLM 抽取本轮信息（容错：失败不影响流程）
        try:
            extracted = await self.llm.extract_profile_info(user_message)
        except Exception:
            extracted = {}

        # 2. 加载已有画像
        profile = await self._load_profile(student_id)

        # 3. 合并：数值维度 EWMA，文本维度直接覆盖
        merged = dict(profile)
        for field, value in extracted.items():
            if field not in DIMENSION_FIELDS.values():
                continue
            if value is None:
                continue
            if field in NUMERIC_DIMENSIONS and isinstance(value, (int, float)):
                old = merged.get(field)
                if isinstance(old, (int, float)):
                    merged[field] = ewma_update(float(old), float(value), alpha=0.3)
                else:
                    merged[field] = max(0.0, min(1.0, float(value)))
            elif isinstance(value, str):
                merged[field] = value

        # 4. 持久化
        await self._persist(student_id, merged, profile)

        # 5. 判断缺失维度 + 完成度
        missing_fields = [
            f for f in DIMENSION_FIELDS.values()
            if merged.get(f) in (None, "", float("nan"))
        ]
        total = len(DIMENSION_FIELDS)
        completion = round((total - len(missing_fields)) / total, 2)

        if not missing_fields:
            summary = await self._summarize(merged)
            return {
                "done": True,
                "question": None,
                "profile": merged,
                "summary": summary,
                "completion": completion,
                "extracted": extracted,
            }

        # 6. 仍有缺失 → LLM 生成下一问
        missing_zh = [
            zh for zh, f in DIMENSION_FIELDS.items() if f in missing_fields
        ]
        question = await self.llm.generate_profile_question(missing_zh[:2], merged)
        return {
            "done": False,
            "question": question,
            "profile": merged,
            "completion": completion,
            "extracted": extracted,
        }

    async def _load_profile(self, student_id: str) -> dict[str, Any]:
        """加载画像；优先真实仓储，失败回退空。"""
        if self.repo is None:
            return {}
        method = getattr(self.repo, "get_or_create_profile", None) or getattr(
            self.repo, "get_or_create", None
        )
        if method is None:
            return {}
        try:
            return await method(student_id)
        except Exception:
            return {}

    async def _persist(
        self, student_id: str, merged: dict[str, Any], old: dict[str, Any]
    ) -> None:
        """持久化画像到仓储（仅在有变化时）。"""
        if self.repo is None:
            return
        update_method = getattr(self.repo, "update_profile", None)
        if update_method is None:
            return
        # 只写有值的字段
        updates = {
            f: merged[f]
            for f in DIMENSION_FIELDS.values()
            if merged.get(f) is not None and merged[f] != old.get(f)
        }
        if not updates:
            return
        try:
            await update_method(student_id, updates)
        except Exception:
            pass

    async def _summarize(self, profile: dict[str, Any]) -> str:
        """画像齐全后生成自然语言摘要（FR-009）。"""
        style_map = {"visual": "视觉型", "auditory": "听觉型", "kinesthetic": "动觉型", "reading": "读写型"}
        parts = [
            f"专业是{profile.get('major', '未知')}",
            f"目标是{profile.get('learning_goal', '未知')}",
            f"学习风格偏{style_map.get(profile.get('learning_style'), profile.get('learning_style', '未知'))}",
        ]
        kb = profile.get("knowledge_base")
        if isinstance(kb, (int, float)):
            parts.append(f"当前知识基础约{kb*100:.0f}%")
        return "、".join(parts) + "。"

    def update_dimension(self, old: float, observed: float, alpha: float = 0.3) -> float:
        """对数值型维度做 EWMA 更新（§7.3.1）。"""
        return ewma_update(old, observed, alpha)

    async def _generate_question(self, missing: list[str], profile: dict[str, Any]) -> str:
        """针对缺失维度生成下一个引导问题（兼容旧调用）。"""
        return await self.llm.generate_profile_question(missing[:2], profile)
