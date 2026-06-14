"""统一日志配置（标准库 logging）。

全项目统一用标准库 logging（与 ``agents.base`` / ``llm.spark_client`` 一致），
不引入第三方日志依赖。``setup_logging`` 配置根 logger 的级别与格式，
``logger`` 供需要模块级 logger 的旧代码导入。
"""

from __future__ import annotations

import logging
import sys

from app.core.config import settings

#: 兼容旧导入（``from app.core.logging import logger``）的模块级 logger
logger = logging.getLogger("app")


def setup_logging() -> None:
    """配置根 logger：按 debug 切换级别，输出到 stdout。

    幂等：重复调用不会叠加 handler。
    """
    level = logging.DEBUG if settings.debug else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    # 避免重复添加 handler（lifespan 多次触发 / reload 场景）
    if any(getattr(h, "_app_handler", False) for h in root.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler._app_handler = True  # type: ignore[attr-defined]
    root.addHandler(handler)


__all__ = ["logger", "setup_logging"]
