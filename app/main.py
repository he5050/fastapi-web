from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth_router import router as auth_router
from app.api.health_router import router as health_router
from app.api.log_router import router as log_router
from app.api.user_router import router as user_router
from app.core.config import print_config_info, settings
from app.core.exceptions import AppError, global_exception_handler
from app.core.logger import get_logger, setup_structlog
from app.db.init_db import run_init_db
from app.db.session import check_db_connection
from app.middleware.logging_middleware import LoggingMiddleware

# 导入日志模型以确保表结构被创建
from app.models.log_model import SysLog  # noqa


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 初始化结构化日志
    setup_structlog()
    logger = get_logger(__name__)

    # 启动时
    logger.info("正在启动应用", app_name=settings.APP_NAME, env=settings.APP_ENV)
    print_config_info()

    # 根据配置执行数据库初始化
    if settings.DB_INIT:
        await run_init_db()

    await check_db_connection()
    # 初始化缓存
    try:
        from redis import asyncio as aioredis
        from fastapi_cache import FastAPICache
        from fastapi_cache.backends.redis import RedisBackend

        # 构建Redis连接URL
        if settings.REDIS_PASSWORD:
            redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        else:
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

        # 创建Redis客户端实例
        redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        # 初始化FastAPICache，传入Redis客户端对象而非字符串
        FastAPICache.init(
            RedisBackend(redis_client),
            prefix="fastapi-cache",
            expire=60,  # 默认过期时间（秒）
            enable=True,  # 启用缓存
        )
        logger.info(
            "缓存服务初始化成功",
            redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        )
    except ImportError:
        logger.warning("fastapi-cache2 未安装，缓存功能已禁用。")
    except Exception as e:
        logger.error("缓存服务连接失败", error=str(e))
    logger.info("应用启动成功")
    yield
    # 关闭时
    logger.info("应用正在关闭...")


app = FastAPI(
    title=settings.APP_NAME,
    description="基于 FastAPI 的分层架构用户管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 注册全局异常处理
app.add_exception_handler(AppError, global_exception_handler)
app.add_exception_handler(HTTPException, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)
app.add_exception_handler(RequestValidationError, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 注册路由
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(health_router)
app.include_router(log_router)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"欢迎使用 {settings.APP_NAME}", "env": settings.APP_ENV}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="127.0.0.1", port=settings.APP_PORT, reload=settings.DEBUG
    )
