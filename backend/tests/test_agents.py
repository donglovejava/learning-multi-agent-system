"""Agent 单元测试。

验证各 Agent 的 run 方法能正确处理 state 并返回增量更新。
"""

import pytest
from app.agents.base import AgentState
from app.agents.orchestrator import OrchestratorAgent
from app.agents.document_agent import DocumentAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.mindmap_agent import MindMapAgent
from app.agents.code_agent import CodeAgent
from app.agents.reading_agent import ReadingAgent
from app.agents.review_agent import ReviewAgent
from app.llm.spark_client import SparkLLMClient


class MockLLM(SparkLLMClient):
    """模拟 LLM 客户端，返回固定文本。"""

    def __init__(self):
        pass  # 跳过父类初始化

    async def chat(self, prompt, **kwargs):
        return "这是模拟的 LLM 回复内容。" * 10

    async def classify_intent(self, user_input):
        return "generate_resource"

    async def extract_knowledge(self, user_input):
        return "Transformer"


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def base_state():
    return AgentState(
        student_id="test-001",
        user_input="我想学 Transformer",
        intent="generate_resource",
        knowledge_point="Transformer注意力机制",
        resource_types=["document"],
        scaffold_level="medium",
        errors=[],
    )


@pytest.mark.anyio
async def test_orchestrator_classify_intent(mock_llm, base_state):
    """Orchestrator 应能分类意图。"""
    agent = OrchestratorAgent(mock_llm)
    base_state["intent"] = None  # 强制重新分类
    result = await agent.run(base_state)
    assert "intent" in result
    assert result["intent"] in {"build_profile", "generate_resource", "plan_path", "assess", "chat"}


@pytest.mark.anyio
async def test_document_agent_generates_content(mock_llm, base_state):
    """Document Agent 应生成文档内容。"""
    agent = DocumentAgent(mock_llm)
    result = await agent.run(base_state)
    assert "document" in result
    doc = result["document"]
    assert doc["type"] == "document"
    assert len(doc["content"]) > 50


@pytest.mark.anyio
async def test_quiz_agent_generates_questions(mock_llm, base_state):
    """Quiz Agent 应生成题目列表。"""
    agent = QuizAgent(mock_llm)
    base_state["resource_types"] = ["quiz"]
    result = await agent.run(base_state)
    assert "quiz" in result
    quiz = result["quiz"]
    assert quiz["type"] == "quiz"
    assert "questions" in quiz["content"] or "questions" in quiz


@pytest.mark.anyio
async def test_mindmap_agent_generates_tree(mock_llm, base_state):
    """MindMap Agent 应生成层次结构。"""
    agent = MindMapAgent(llm=mock_llm)
    base_state["resource_types"] = ["mindmap"]
    result = await agent.run(base_state)
    assert "mindmap" in result
    tree = result["mindmap"]["data"]
    assert "root" in tree


@pytest.mark.anyio
async def test_code_agent_generates_runnable_code(mock_llm, base_state):
    """Code Agent 应生成可编译的 Python 代码。"""
    agent = CodeAgent(mock_llm)
    base_state["resource_types"] = ["code"]
    result = await agent.run(base_state)
    assert "code" in result
    code_res = result["code"]
    assert code_res["type"] == "code"
    assert code_res.get("runnable", False) is True


@pytest.mark.anyio
async def test_reading_agent_generates_content(mock_llm, base_state):
    """Reading Agent 应生成拓展阅读内容。"""
    agent = ReadingAgent(mock_llm)
    base_state["resource_types"] = ["reading"]
    result = await agent.run(base_state)
    assert "reading" in result
    reading = result["reading"]
    assert reading["type"] == "reading"
    assert len(reading["content"]) > 50


@pytest.mark.anyio
async def test_review_agent_passes_valid_content(mock_llm, base_state):
    """Review Agent 应通过有参考资料的文档。"""
    agent = ReviewAgent(mock_llm)
    base_state["document"] = {"type": "document", "content": "测试内容"}
    base_state["retrieved_context"] = [{"content": "参考资料"}]
    result = await agent.run(base_state)
    assert "review_result" in result
    assert result["review_result"]["passed"] is True
