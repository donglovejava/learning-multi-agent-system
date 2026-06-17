"""讯飞星火大模型客户端封装。

走 HTTP OpenAI 兼容版（``{base_url}/v1/chat/completions``），鉴权使用
控制台「http服务接口认证信息」中的 APIPassword 作为 Bearer token（§5.2.1）。

提供同步/流式对话、意图分类、知识点抽取接口，内置失败重试与指数退避。
所有 Agent 通过本客户端访问 LLM，便于统一管理鉴权、超时与降级。

``embed`` 仍为占位：OpenAI 兼容端点不含向量化，需走讯飞独立的文本向量化
接口，接入 Milvus 检索时再实现（§6.3）。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

#: OpenAI 兼容对话端点（相对 base_url）
CHAT_PATH = "/v1/chat/completions"

#: 合法意图标签（§4.2.1）
INTENTS = {"build_profile", "generate_resource", "plan_path", "assess", "chat"}


class LLMError(Exception):
    """LLM 调用异常。"""


class SparkLLMClient:
    """讯飞星火大模型客户端（HTTP OpenAI 兼容版）。

    Args:
        api_password: 控制台 APIPassword；缺省读取配置 ``spark_api_password``。
        base_url: 服务根地址。
        model: 模型名（Spark Lite 为 ``"lite"``）。
        max_retries: 失败重试次数（§4.5.1 规定 3 次）。
        timeout: 单次请求超时（秒）。
    """

    def __init__(
        self,
        api_password: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        timeout: Optional[float] = None,
    ) -> None:
        self.api_password = api_password or settings.spark_api_password
        self.base_url = (base_url or settings.spark_base_url).rstrip("/")
        self.model = model or settings.spark_model
        self.max_retries = max_retries
        self.timeout = timeout or settings.spark_timeout

    # --- 公共接口 -----------------------------------------------------------

    async def chat(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """同步对话：返回完整回复文本。

        失败自动重试 ``max_retries`` 次，指数退避。全部失败抛 ``LLMError``。
        """
        messages = self._build_messages(prompt, system)
        data = await self._request(messages, temperature=temperature, stream=False)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"星火返回结构异常: {data}") from exc

    async def chat_stream(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """流式对话：逐增量产出，供 SSE 接口转发（§4.4.2）。

        直接消费星火 SSE 流（``stream=true``），按 delta 内容增量 yield。
        流式失败不重试（已产出部分无法回滚），首次连接失败抛 ``LLMError``。
        """
        messages = self._build_messages(prompt, system)
        payload = self._payload(messages, temperature=temperature, stream=True)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", self.base_url + CHAT_PATH, headers=self._headers(), json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        token = self._parse_sse_line(line)
                        if token:
                            yield token
        except httpx.HTTPError as exc:
            raise LLMError(f"星火流式调用失败: {exc}") from exc

    async def classify_intent(self, user_input: str) -> str:
        """意图分类：供 Orchestrator 路由（§4.2.1）。

        返回意图标签之一：build_profile / generate_resource / plan_path / assess / chat。
        无法识别时回退到 ``chat``。
        """
        system = (
            "你是意图分类器。判断用户输入属于以下哪一类，只输出标签本身，不要解释：\n"
            "- build_profile：想构建/完善学习画像、自我介绍、回答画像问题\n"
            "- generate_resource：想学某个知识点、要资料/讲解/练习题/思维导图/代码\n"
            "- plan_path：想规划学习路径/学习计划/学习顺序\n"
            "- assess：想看学习效果/评估报告/掌握情况\n"
            "- chat：其它闲聊或无法归类\n"
            "只输出一个英文标签。"
        )
        try:
            raw = (await self.chat(user_input, system=system, temperature=0.0)).strip().lower()
        except LLMError:
            return "chat"
        for tag in INTENTS:
            if tag in raw:
                return tag
        return "chat"

    async def extract_knowledge(self, user_input: str) -> str:
        """从自然语言中抽取目标知识点（§4.2.1）。

        返回简洁的知识点名词短语；失败或为空时回退原始输入。
        """
        system = (
            "从用户的话里提取他想学习的核心知识点，只输出知识点名称本身，"
            "不要加任何多余文字、标点或解释。例如输入「我想学Transformer的注意力机制」，"
            "输出「Transformer注意力机制」。"
        )
        try:
            result = (await self.chat(user_input, system=system, temperature=0.0)).strip()
        except LLMError:
            return user_input
        return result or user_input

    async def extract_profile_info(self, user_message: str) -> dict[str, Any]:
        """从单轮对话抽取 6 维度画像信息（§4.2.2 / §3.1.1）。

        6 个维度：专业、学习目标、知识基础、学习风格、学习动机、元认知。
        输出严格 JSON，能识别的字段填值，未涉及的字段留 null。
        """
        system = (
            "你是学习画像分析器。从学生的对话中抽取 6 个维度的信息，"
            "严格输出一个 JSON 对象，不要任何额外文字或代码围栏。字段：\n"
            'major(专业，如"计算机")\n'
            'learning_goal(学习目标：考研/期末/竞赛/兴趣/工作)\n'
            'knowledge_base(知识基础，0-1 的浮点数，根据自评估算，未知给null)\n'
            'learning_style(学习风格：视觉/听觉/动觉/读写)\n'
            'motivation(学习动机：内在/外在)\n'
            'metacognition(元认知能力，0-1 浮点数，未知给null)\n'
            "用户没提到的维度填 null。只输出 JSON。"
        )
        try:
            raw = await self.chat(user_message, system=system, temperature=0.0)
        except LLMError:
            return {}
        from app.llm.json_utils import extract_json
        try:
            data = extract_json(raw)
        except ValueError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if v is not None}

    async def generate_profile_question(
        self, missing_dimensions: list[str], profile: dict[str, Any]
    ) -> str:
        """针对缺失维度生成下一个自然引导问题（§4.2.2）。"""
        dims_desc = "、".join(missing_dimensions[:2])
        system = (
            "你是温暖的 AI 学习伙伴。学生画像还缺少以下维度，"
            "请像朋友聊天一样自然地问一个问题，一次只问一个维度。"
            "问题要亲切简短（不超过 30 字），不要像填问卷。"
        )
        prompt = (
            f"还缺少这些维度的信息：{dims_desc}。\n"
            f"学生已有信息：{profile}\n"
            "请生成一个自然亲切的引导问题，只输出问题本身。"
        )
        try:
            question = (await self.chat(prompt, system=system, temperature=0.7)).strip()
        except LLMError:
            target = missing_dimensions[0]
            templates = {
                "专业": "你现在学的是什么专业呀？",
                "学习目标": "你现在的学习目标是什么呢？考研、期末、还是工作？",
                "知识基础": "如果给自己当前的基础打分，1-10 分你打几分？",
                "学习风格": "你更喜欢哪种学习方式？看视频、听课、动手做、还是看书？",
                "学习动机": "是什么让你想学这个呢？兴趣还是目标？",
                "元认知": "你平时会复盘自己的学习过程吗？",
            }
            return templates.get(target, f"能告诉我关于{target}的情况吗？")
        return question or f"能聊聊关于{missing_dimensions[0]}的情况吗？"

    async def embed(self, text: str) -> list[float]:
        """文本向量化：返回 1024 维向量（对齐 BGE-large-zh，§6.3）。

        代理到独立的 EmbeddingClient（讯飞向量化走单独端点，model=emb）。
        """
        from app.llm.embedding_client import EmbeddingClient
        if not hasattr(self, "_embedder"):
            self._embedder = EmbeddingClient(self.api_password, self.base_url)
        return await self._embedder.embed(text)

    # --- 内部实现 -----------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if not self.api_password:
            raise LLMError("未配置 spark_api_password，无法调用星火 HTTP API")
        return {
            "Authorization": f"Bearer {self.api_password}",
            "Content-Type": "application/json",
        }

    def _payload(
        self, messages: list[dict[str, str]], *, temperature: float, stream: bool
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }

    @staticmethod
    def _build_messages(prompt: str, system: Optional[str]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def _request(
        self, messages: list[dict[str, str]], *, temperature: float, stream: bool
    ) -> dict[str, Any]:
        """执行非流式 HTTP 调用，失败指数退避重试。"""
        payload = self._payload(messages, temperature=temperature, stream=stream)
        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        self.base_url + CHAT_PATH, headers=self._headers(), json=payload
                    )
                    resp.raise_for_status()
                    data = resp.json()
                self._check_business_error(data)
                return data
            except Exception as exc:  # noqa: BLE001 - 统一兜底重试
                last_err = exc
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "星火调用失败 (第 %d/%d 次)，%.0fs 后重试: %s",
                    attempt, self.max_retries, wait, exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(wait)
        raise LLMError(f"星火调用在 {self.max_retries} 次重试后仍失败") from last_err

    @staticmethod
    def _check_business_error(data: dict[str, Any]) -> None:
        """检查星火业务错误码（HTTP 200 但 code != 0 的情况）。"""
        code = data.get("code")
        if code not in (None, 0):
            raise LLMError(f"星火业务错误 code={code}: {data.get('message')}")

    @staticmethod
    def _parse_sse_line(line: str) -> str:
        """解析一行 SSE，返回增量文本（无内容返回空串）。"""
        if not line or not line.startswith("data:"):
            return ""
        chunk = line[len("data:"):].strip()
        if not chunk or chunk == "[DONE]":
            return ""
        try:
            obj = json.loads(chunk)
            return obj["choices"][0]["delta"].get("content", "") or ""
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return ""
