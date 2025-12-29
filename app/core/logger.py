import logging
import sys

import structlog

from app.core.config import settings


def setup_structlog():
    """
    配置结构化日志
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S%f"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准 logging 作为 structlog 的底层
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        force=True,
    )


def get_logger(name: str = "app"):
    """
    获取结构化logger实例

    Args:
        name: logger名称，默认为"app"

    Returns:
        structlog logger实例
    """
    return structlog.get_logger(name)


# 初始化日志配置
setup_structlog()

# 导出默认 logger
logger = get_logger()
