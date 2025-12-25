import logging
import sys
from app.core.config import settings


def setup_logger():
    """
    配置全局日志
    """
    logger = logging.getLogger("app")
    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logger()
