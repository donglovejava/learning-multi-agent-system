"""LangGraph 编排引擎（§2.1.1 / §4.3）。

将 11 个 Agent 组织为有向图，按意图驱动两类核心协作流程：

1. **综合资源生成**（§4.3.1）：
   Orchestrator → Profile → Retrieval → [Document/Quiz/MindMap/Code 并行] → Review

2. **学习路径规划**（§4.3.2）：
   Orchestrator → Profile → Retrieval → Path → Review

设计要点：
- 资源生成节点并行 fan-out / fan-in，吞吐量↑3-5 倍（附录 A IN-01）。
- 单 Agent 故障被 ``BaseAgent`` 隔离为 ``errors`` 累积，不中断整图（§4.5.2）。
- 共享 ``AgentState`` 在节点间流转，节点只读取所需字段、写回自身产出。

骨架阶段：``build_graph`` 在已安装 langgraph 时构建真实 ``StateGraph``；
未安装时回退到 ``SequentialGraph`` 轻量实现，保证流程可端到端跑通与测试。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from app.agents.base import AgentState, BaseAgent

logger = logging.getLogger(__name__)

#: 意图 → 参与的资源生成 Agent 名称（fan-out 分支）
RESOURCE_AGENTS = {"document", "quiz", "mindmap", "code", "reading"}


class AgentRegistry:
    """Agent 实例容器：按名称注册/查找，供编排图调度。"""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise KeyError(f"未注册的 Agent: {name}")
        return self._agents[name]

    def has(self, name: str) -> bool:
        return name in self._agents


class SequentialGraph:
    """轻量编排回退实现（无 langgraph 依赖时使用）。

    按 §4.3 的拓扑顺序执行；资源生成阶段对启用的资源 Agent 做并行 fan-out。
    与 LangGraph 版本对上层 ``invoke`` 接口一致，便于无缝切换。
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    async def invoke(self, state: AgentState) -> AgentState:
        state = dict(state)  # 拷贝，避免污染入参

        # 1. Orchestrator：意图识别 + 知识点抽取
        state.update(await self._run("orchestrator", state))
        intent = state.get("intent", "chat")

        # 2. Profile：装载/构建画像
        if self.registry.has("profile"):
            state.update(await self._run("profile", state))

        if intent == "generate_resource":
            await self._run_resource_flow(state)
        elif intent == "plan_path":
            await self._run_path_flow(state)
        elif intent == "build_profile":
            pass  # 画像构建已在 Profile 节点完成
        # intent == "assess" / "chat" 等由各自端点直接调用对应 Agent

        return state  # type: ignore[return-value]

    async def _run_resource_flow(self, state: AgentState) -> None:
        """综合资源生成流程（§4.3.1）。"""
        if self.registry.has("retrieval"):
            state.update(await self._run("retrieval", state))

        # fan-out：并行运行选中的资源 Agent
        selected = [
            name for name in state.get("resource_types", [])
            if name in RESOURCE_AGENTS and self.registry.has(name)
        ]
        results = await asyncio.gather(
            *(self._run(name, state) for name in selected),
            return_exceptions=False,
        )
        # fan-in：合并各资源产出
        for update in results:
            state.update(update)

        # Video 走异步任务，单独触发（不阻塞 30s 主流程，§7.2.1）
        if "video" in state.get("resource_types", []) and self.registry.has("video"):
            state.update(await self._run("video", state))

        # 统一审核
        if self.registry.has("review"):
            state.update(await self._run("review", state))

    async def _run_path_flow(self, state: AgentState) -> None:
        """学习路径规划流程（§4.3.2）。"""
        if self.registry.has("retrieval"):
            state.update(await self._run("retrieval", state))
        if self.registry.has("path"):
            state.update(await self._run("path", state))
        if self.registry.has("review"):
            state.update(await self._run("review", state))

    async def _run(self, name: str, state: AgentState) -> dict[str, Any]:
        return await self.registry.get(name)(state)


def build_graph(registry: AgentRegistry) -> Any:
    """构建编排图。

    优先使用 langgraph 的 ``StateGraph``；不可用时回退 ``SequentialGraph``。
    两者均暴露 ``invoke(state) -> state`` 协程接口。
    """
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        logger.warning("未检测到 langgraph，使用 SequentialGraph 回退实现")
        return SequentialGraph(registry)

    return _build_langgraph(registry, StateGraph, END)


def _build_langgraph(
    registry: AgentRegistry,
    state_graph_cls: Any,
    end: Any,
) -> Any:
    """用 langgraph StateGraph 构建条件路由图（§4.3）。"""
    graph = state_graph_cls(AgentState)

    # 注册节点：包装为可调用，缺失的 Agent 跳过
    def node(name: str) -> Callable[[AgentState], Awaitable[dict[str, Any]]]:
        async def _node(state: AgentState) -> dict[str, Any]:
            return await registry.get(name)(state)
        return _node

    for name in ("orchestrator", "profile", "retrieval",
                 "document", "quiz", "mindmap", "code", "video",
                 "path", "assessment", "review"):
        if registry.has(name):
            graph.add_node(name, node(name))

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "profile")

    def route_after_profile(state: AgentState) -> str:
        intent = state.get("intent", "chat")
        if intent == "generate_resource":
            return "retrieval"
        if intent == "plan_path":
            return "retrieval"
        return end

    graph.add_conditional_edges(
        "profile",
        route_after_profile,
        {"retrieval": "retrieval", end: end},
    )

    # retrieval 之后按意图分流到资源生成或路径规划
    def route_after_retrieval(state: AgentState) -> str:
        return "path" if state.get("intent") == "plan_path" else "document"

    graph.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {"path": "path", "document": "document"},
    )

    # 资源生成链（langgraph 顺序近似并行，真正并行见 SequentialGraph）
    graph.add_edge("document", "quiz")
    graph.add_edge("quiz", "mindmap")
    graph.add_edge("mindmap", "code")
    graph.add_edge("code", "review")
    graph.add_edge("path", "review")
    graph.add_edge("review", end)

    return graph.compile()
