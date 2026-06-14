"""创新三：知识脚手架动态生成（IN-07）。

3 级脚手架（高/中/低支持）+ 随能力提升动态调整。
对应设计说明书 3.3 节。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


class ScaffoldLevel(str, Enum):
    HIGH = "high"      # 高支持（初学者，掌握度 <50%）
    MEDIUM = "medium"  # 中支持（进阶者，50-80%）
    LOW = "low"        # 低支持（高级者，>80%）


@dataclass
class ScaffoldConfig:
    level: ScaffoldLevel
    include_steps: bool
    include_hints: bool
    example_type: str       # concrete / abstract / none
    explanation_depth: str  # detailed / moderate / minimal
    practice_type: str      # guided / semi_guided / independent
    include_challenge: bool = False


@dataclass
class ScaffoldContent:
    knowledge_point: str
    level: ScaffoldLevel
    steps: Optional[List[str]] = None
    hints: Optional[List[str]] = None
    examples: Optional[List[Dict]] = None
    explanation: Optional[str] = None
    practice: Optional[Dict] = None
    challenge: Optional[Dict] = None


_CONFIGS: Dict[ScaffoldLevel, ScaffoldConfig] = {
    ScaffoldLevel.HIGH: ScaffoldConfig(
        ScaffoldLevel.HIGH, True, True, "concrete", "detailed", "guided", False
    ),
    ScaffoldLevel.MEDIUM: ScaffoldConfig(
        ScaffoldLevel.MEDIUM, True, False, "abstract", "moderate", "semi_guided", False
    ),
    ScaffoldLevel.LOW: ScaffoldConfig(
        ScaffoldLevel.LOW, False, False, "none", "minimal", "independent", True
    ),
}

_ORDER = [ScaffoldLevel.HIGH, ScaffoldLevel.MEDIUM, ScaffoldLevel.LOW]


class ScaffoldGenerator:
    """脚手架动态生成器。

    脚手架的「策略」由本类确定；真实文本内容可交给 LLM 客户端生成。
    传入的 llm_client 为可选——缺省时使用内置模板，保证可独立运行与测试。
    """

    def __init__(self, llm_client=None) -> None:
        self.llm = llm_client

    def determine_level(self, mastery: float) -> ScaffoldLevel:
        if mastery < 0.5:
            return ScaffoldLevel.HIGH
        if mastery < 0.8:
            return ScaffoldLevel.MEDIUM
        return ScaffoldLevel.LOW

    def generate(self, knowledge_point: str, student_mastery: float) -> ScaffoldContent:
        level = self.determine_level(student_mastery)
        config = _CONFIGS[level]
        content = ScaffoldContent(knowledge_point=knowledge_point, level=level)
        if config.include_steps:
            content.steps = self._steps(knowledge_point, level)
        if config.include_hints:
            content.hints = self._hints(knowledge_point)
        if config.example_type != "none":
            content.examples = self._examples(knowledge_point, config.example_type)
        content.explanation = self._explanation(knowledge_point, config.explanation_depth)
        content.practice = self._practice(knowledge_point, config.practice_type)
        if config.include_challenge:
            content.challenge = self._challenge(knowledge_point)
        logger.info("生成 %s 级脚手架: %s (掌握度=%.2f)", level.value, knowledge_point, student_mastery)
        return content

    def adjust_level(
        self, current: ScaffoldLevel, recent_performance: float, trend: str
    ) -> ScaffoldLevel:
        if recent_performance > 0.8 and trend == "improving":
            return self._upgrade(current)
        if recent_performance < 0.5 or trend == "declining":
            return self._downgrade(current)
        return current

    def _upgrade(self, current: ScaffoldLevel) -> ScaffoldLevel:
        idx = _ORDER.index(current)
        return _ORDER[idx + 1] if idx < len(_ORDER) - 1 else current

    def _downgrade(self, current: ScaffoldLevel) -> ScaffoldLevel:
        idx = _ORDER.index(current)
        return _ORDER[idx - 1] if idx > 0 else current

    def _steps(self, k: str, level: ScaffoldLevel) -> List[str]:
        if level == ScaffoldLevel.HIGH:
            return [
                f"步骤 1：阅读 {k} 的核心概念定义",
                "步骤 2：查看具体示例，理解概念的应用",
                "步骤 3：按照提示完成引导式练习",
                "步骤 4：独立完成类似题目，检验理解程度",
            ]
        return [
            f"步骤 1：理解 {k} 的核心概念",
            "步骤 2：查看抽象示例，思考应用场景",
            "步骤 3：完成练习题",
        ]

    def _hints(self, k: str) -> List[str]:
        return [
            f"提示：注意 {k} 的关键公式推导过程",
            "提示：可以参考下面的具体示例",
            "提示：如果遇到困难，回顾步骤 1 的核心概念",
        ]

    def _examples(self, k: str, example_type: str) -> List[Dict]:
        if example_type == "concrete":
            return [{"title": f"{k} 的具体示例", "content": "假设我们要解决一个具体问题……", "difficulty": "easy"}]
        return [{"title": f"{k} 的抽象示例", "content": f"考虑一般情况下的 {k}……", "difficulty": "medium"}]

    def _explanation(self, k: str, depth: str) -> str:
        if depth == "detailed":
            return f"{k} 是本课程的重要概念。它指的是……（详细解释）。理解这个概念对后续学习至关重要。"
        if depth == "moderate":
            return f"{k} 指的是……（适度解释）。"
        return f"关于 {k}，请参考教材相关章节。"

    def _practice(self, k: str, practice_type: str) -> Dict:
        descs = {
            "guided": (f"按照提示完成 {k} 的练习", True),
            "semi_guided": (f"完成 {k} 的练习", False),
            "independent": (f"独立完成 {k} 的综合练习", False),
        }
        desc, hints = descs[practice_type]
        return {"type": practice_type, "description": desc, "hints_available": hints}

    def _challenge(self, k: str) -> Dict:
        return {
            "question": f"请自主探索 {k} 在实际项目中的应用",
            "requirement": "写出至少 3 个实际应用场景，并分析优缺点",
            "evaluation_criteria": ["应用场景的合理性", "分析的深度", "创新性"],
        }
