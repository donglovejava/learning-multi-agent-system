"""健康检查与基础路由测试。"""

import pytest


@pytest.mark.anyio
async def test_health(client):
    """健康检查端点应返回 200 和 app 信息。"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "env" in data


@pytest.mark.anyio
async def test_openapi_schema(client):
    """OpenAPI 文档端点应可用。"""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "info" in schema
    assert "paths" in schema
    # 验证核心端点存在
    assert "/api/v1/chat" in schema["paths"]
    assert "/api/v1/resources" in schema["paths"]
    assert "/api/v1/path" in schema["paths"]
