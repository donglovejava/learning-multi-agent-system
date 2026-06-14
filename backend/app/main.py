"""FastAPI 应用入口（§2.1 / §8.1）。

装配中间件、路由与生命周期。CORS 面向前端（§2.3.2），结构化日志见 ``core.logging``。

启动方式：``uvicorn app.main:app --host 0.0.0.0 --port 8000``
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化日志与编排图，关闭时释放资源。"""
    setup_logging()
    # 预热编排图，使首个请求不承担构造开销
    from app.dependencies import get_orchestration

    get_orchestration()
    yield
    # 关闭钩子（DB/MQ 连接释放）在接入真实依赖后补充


app = FastAPI(
    title=settings.app_name,
    description="基于大模型的个性化资源生成与学习多智能体系统",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
