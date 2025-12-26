from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.config import settings, print_config_info
from app.core.exceptions import global_exception_handler, AppError
from app.db.session import check_db_connection
from app.api.user_router import router as user_router
from contextlib import asynccontextmanager
from app.db.init_db import run_init_db
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时
    print_config_info()

    # 根据配置执行数据库初始化
    if settings.DB_INIT:
        await run_init_db()

    await check_db_connection()
    yield
    # 关闭时
    print("🛑 应用正在关闭...")


app = FastAPI(
    title=settings.APP_NAME,
    description="基于 FastAPI 的分层架构用户管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册全局异常处理
app.add_exception_handler(AppError, global_exception_handler)
app.add_exception_handler(HTTPException, global_exception_handler)
app.add_exception_handler(RequestValidationError, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 注册路由
app.include_router(user_router)


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"欢迎使用 {settings.APP_NAME}", "env": settings.APP_ENV}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="127.0.0.1", port=settings.APP_PORT, reload=settings.DEBUG
    )
