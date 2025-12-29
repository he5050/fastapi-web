import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.session import Base, engine
from app.models.log_model import SysLog  # noqa

# 导入模型以确保 Base.metadata 包含所有表
from app.models.user_model import User  # noqa


async def create_database_if_not_exists():
    """
    如果数据库不存在，则创建它
    """
    # 构造不含数据库名称的连接 URL
    tmp_url = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/"
    tmp_engine = create_async_engine(tmp_url, isolation_level="AUTOCOMMIT")

    async with tmp_engine.connect() as conn:
        print(f"🔍 检查数据库 '{settings.DB_NAME}' 是否存在...")
        sql = text(
            f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET {settings.DB_CHARSET}"
        )
        await conn.execute(sql)

    await tmp_engine.dispose()
    print(f"✅ 数据库 '{settings.DB_NAME}' 检查/创建完成")


async def init_models():
    """
    初始化数据库表结构
    """
    print("🚀 开始同步模型到数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 所有表结构初始化完成")


async def run_init_db():
    """
    供应用启动时调用的统一初始化函数
    """
    print("=" * 50)
    print("🛠️  正在执行数据库自动初始化...")
    try:
        await create_database_if_not_exists()
        await init_models()
        print("✨ 数据库巡检与初始化任务执行成功！")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        # 这里可以选择抛出异常阻止启动，或者仅记录日志
        raise e
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_init_db())
