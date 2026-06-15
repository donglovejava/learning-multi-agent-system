"""资源生成端到端测试。

验证 POST /api/v1/resources 能真实调用讯飞星火并返回多种资源。
依赖：讯飞星火 API 已配置（.env 中 SPARK_API_PASSWORD）。
"""

import pytest


@pytest.mark.anyio
async def test_generate_resources_document(client, sample_student_id, sample_knowledge):
    """生成讲解文档应返回 200 且 content 非空。"""
    resp = await client.post(
        "/api/v1/resources",
        json={
            "student_id": sample_student_id,
            "knowledge_point": sample_knowledge,
            "resource_types": ["document"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "resources" in data
    assert len(data["resources"]) > 0
    doc = data["resources"][0]
    assert doc["type"] == "document"
    assert len(doc.get("content", "")) > 100  # 至少 100 字符


@pytest.mark.anyio
async def test_generate_resources_quiz(client, sample_student_id, sample_knowledge):
    """生成练习题应返回 200 且题目结构完整。"""
    resp = await client.post(
        "/api/v1/resources",
        json={
            "student_id": sample_student_id,
            "knowledge_point": sample_knowledge,
            "resource_types": ["quiz"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    quiz = data["resources"][0]
    assert quiz["type"] == "quiz"
    questions = quiz.get("content", {}).get("questions", [])
    assert len(questions) >= 5  # 至少 5 道题
    # 验证题目结构
    q = questions[0]
    assert "question" in q
    assert "options" in q
    assert "answer" in q
    assert "explanation" in q


@pytest.mark.anyio
async def test_generate_resources_mindmap(client, sample_student_id, sample_knowledge):
    """生成思维导图应返回 200 且有层次结构。"""
    resp = await client.post(
        "/api/v1/resources",
        json={
            "student_id": sample_student_id,
            "knowledge_point": sample_knowledge,
            "resource_types": ["mindmap"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    mindmap = data["resources"][0]
    assert mindmap["type"] == "mindmap"
    tree = mindmap.get("content", {}).get("data", {})
    assert "root" in tree
    assert "label" in tree["root"]


@pytest.mark.anyio
async def test_generate_resources_code(client, sample_student_id, sample_knowledge):
    """生成代码案例应返回 200 且代码可编译。"""
    resp = await client.post(
        "/api/v1/resources",
        json={
            "student_id": sample_student_id,
            "knowledge_point": sample_knowledge,
            "resource_types": ["code"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    code_res = data["resources"][0]
    assert code_res["type"] == "code"
    assert code_res.get("content", {}).get("runnable", False) is True


@pytest.mark.anyio
async def test_generate_resources_reading(client, sample_student_id, sample_knowledge):
    """生成拓展阅读应返回 200 且有内容。"""
    resp = await client.post(
        "/api/v1/resources",
        json={
            "student_id": sample_student_id,
            "knowledge_point": sample_knowledge,
            "resource_types": ["reading"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    reading = data["resources"][0]
    assert reading["type"] == "reading"
    assert len(reading.get("content", "")) > 50


@pytest.mark.anyio
async def test_generate_resources_multiple(client, sample_student_id, sample_knowledge):
    """一次请求生成多种资源应全部返回。"""
    resp = await client.post(
        "/api/v1/resources",
        json={
            "student_id": sample_student_id,
            "knowledge_point": sample_knowledge,
            "resource_types": ["document", "quiz", "mindmap", "code", "reading"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["resources"]) == 5
    types = {r["type"] for r in data["resources"]}
    assert types == {"document", "quiz", "mindmap", "code", "reading"}
    # 验证耗时合理（< 60s）
    assert data["generation_time"] < 60
