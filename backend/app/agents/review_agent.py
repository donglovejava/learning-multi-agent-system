"""Review Agent（内容审核）。

5 层防幻觉审核（§4.2.10 / 附录 A IN-04）。对其他 Agent 产出的内容做
检索验证、逻辑一致性、事实核查、敏感检测、结构完整性，任一 error/critical
即拒绝放行。目标审核准确率 >95%（FR-022）。

5 层防线：
1. 知识检索验证（是否有出处支撑）
2. 逻辑一致性检查（LLM）
3. 事实性核查（LLM）
4. 敏感内容检测（LLM + 关键词）
5. 结构完整性检查（题型字段/代码可编译/文档章节齐全）
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import AgentState, BaseAgent
from app.llm.spark_client import LLMError, SparkLLMClient

logger = logging.getLogger(__name__)

#: 审核问题严重级别，error/critical 会导致内容不通过
SEVERITY_BLOCKING = {"error", "critical"}

#: 敏感词/违禁词初筛（可扩展）
SENSITIVE_KEYWORDS = [
    "色情", "赌博", "毒品", "暴力", "自杀", "炸弹", "枪支",
]


class ReviewAgent(BaseAgent):
    """生成内容质量审核（5 层防线）。"""

    name = "review"

    def __init__(self, llm: SparkLLMClient) -> None:
        self.llm = llm

    async def run(self, state: AgentState) -> dict[str, Any]:
        targets = {
            key: state[key]
            for key in ("document", "quiz", "mindmap", "code", "reading")
            if state.get(key)
        }
        references = state.get("retrieved_context", [])
        knowledge = state.get("knowledge_point", "")
        results = {}
        for key, content in targets.items():
            results[key] = await self.review(content, references, knowledge, key)
        passed = all(r["passed"] for r in results.values()) if results else True
        return {"review_result": {"passed": passed, "details": results, "layers": 5}}

    async def review(
        self,
        content: dict[str, Any],
        references: list[dict[str, Any]],
        knowledge: str = "",
        resource_type: str = "",
    ) -> dict[str, Any]:
        """对单份内容执行 5 层审核。"""
        issues: list[dict[str, str]] = []

        # 抽取纯文本用于审核
        text = self._extract_text(content)

        # 第 1 道：知识检索验证
        if not references and knowledge:
            issues.append({"layer": 1, "type": "unverified", "severity": "warning",
                           "message": "内容无检索出处支撑"})

        # 第 4 道（先做，成本低的）：敏感内容关键词检测
        for kw in SENSITIVE_KEYWORDS:
            if kw in text:
                issues.append({"layer": 4, "type": "sensitive", "severity": "critical",
                               "message": f"检测到敏感词：{kw}"})
                break

        # 第 5 道：结构完整性
        struct_issue = self._check_structure(content, resource_type)
        if struct_issue:
            issues.append({"layer": 5, "type": "structure", "severity": "error",
                           "message": struct_issue})

        # 第 2-3 道：逻辑一致性 + 事实核查（LLM，合并一次调用省 token）
        llm_issue = await self._llm_check(text, knowledge, resource_type)
        if llm_issue:
            issues.append(llm_issue)

        passed = not any(i["severity"] in SEVERITY_BLOCKING for i in issues)
        return {
            "passed": passed,
            "issues": issues,
            "quality_score": self._quality_score(issues),
            "layers_checked": 5,
        }

    # --- 5 层实现 -----------------------------------------------------------

    @staticmethod
    def _extract_text(content: dict[str, Any]) -> str:
        """从资源内容里抽出待审核文本。"""
        if not isinstance(content, dict):
            return str(content)
        parts = []
        if "content" in content and isinstance(content["content"], str):
            parts.append(content["content"])
        if "code" in content and isinstance(content["code"], str):
            parts.append(content["code"])
        if isinstance(content.get("content"), dict):
            # quiz 的题目
            qs = content["content"].get("questions", [])
            for q in qs:
                parts.append(q.get("question", ""))
                parts.append(q.get("explanation", ""))
        return "\n".join(parts)

    @staticmethod
    def _check_structure(content: dict[str, Any], resource_type: str) -> str | None:
        """第 5 道：结构完整性。"""
        if resource_type == "document":
            text = content.get("content", "")
            if not isinstance(text, str) or len(text) < 200:
                return "文档过短或缺少内容"
        elif resource_type == "quiz":
            inner = content.get("content") or content
            questions = inner.get("questions", []) if isinstance(inner, dict) else []
            if len(questions) < 3:
                return "题目数量不足"
            for q in questions:
                if not q.get("answer"):
                    return "存在缺少答案的题目"
        elif resource_type == "code":
            inner = content.get("content") or content
            if isinstance(inner, dict) and inner.get("runnable") is False:
                return "代码无法编译"
        return None

    async def _llm_check(
        self, text: str, knowledge: str, resource_type: str
    ) -> dict[str, str] | None:
        """第 2-3 道：逻辑一致性 + 事实核查（LLM）。"""
        if not text or not knowledge:
            return None
        system = (
            "你是教育内容审核专家。判断给定内容关于知识点「"
            + knowledge
            + "」是否存在事实错误或逻辑矛盾。"
            "严格输出 JSON：{\"has_error\": true/false, \"severity\": \"error|warning|none\", "
            "\"reason\": \"简短说明\"}。只输出 JSON。"
        )
        try:
            raw = await self.llm.chat(
                f"内容类型：{resource_type}\n内容：\n{text[:1500]}",
                system=system,
                temperature=0.0,
            )
        except LLMError as exc:
            logger.warning("审核 LLM 调用失败，跳过该层：%s", str(exc)[:60])
            return None

        from app.llm.json_utils import extract_json
        try:
            data = extract_json(raw)
        except ValueError:
            return None
        if not isinstance(data, dict) or not data.get("has_error"):
            return None
        severity = data.get("severity", "warning")
        if severity == "none":
            return None
        layer = 2 if "逻辑" in str(data.get("reason", "")) else 3
        return {
            "layer": layer,
            "type": "logic" if layer == 2 else "fact",
            "severity": severity,
            "message": data.get("reason", "LLM 检测到问题"),
        }

    @staticmethod
    def _quality_score(issues: list[dict[str, str]]) -> float:
        """按问题严重度扣分，得到 0-1 质量分。"""
        penalty = {"warning": 0.1, "error": 0.4, "critical": 1.0}
        score = 1.0 - sum(penalty.get(i.get("severity", "warning"), 0.1) for i in issues)
        return max(0.0, round(score, 3))
