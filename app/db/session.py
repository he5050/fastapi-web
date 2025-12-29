import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# 配置 SQLAlchemy 日志
logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 创建异步引擎
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# 基础模型类
class Base(declarative_base()):
    __abstract__ = True


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库异步会话的依赖项
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """
    检查数据库连接状态 (启动时调用)
    """
    try:

        async with engine.connect() as conn:
            _ = await conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功!")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print(f"🔍 尝试连接的地址: {settings.async_database_url}")
        return False
