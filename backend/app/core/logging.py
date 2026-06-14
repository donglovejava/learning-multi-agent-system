"""统一日志配置（loguru）。"""
import sys
from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    logger.remove()
    level = "DEBUG" if settings.debug else "INFO"
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,
    )
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level=level,
        encoding="utf-8",
        enqueue=True,
    )


__all__ = ["logger", "setup_logging"]
