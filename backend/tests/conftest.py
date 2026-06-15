"""后端测试配置与公共 fixture。"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """FastAPI 异步测试客户端。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_student_id():
    return "test-student-001"


@pytest.fixture
def sample_knowledge():
    return "Transformer注意力机制"
