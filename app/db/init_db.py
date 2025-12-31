import asyncio
import bcrypt

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import AsyncSessionLocal, Base, engine
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


async def create_super_admin():
    """
    创建超级管理员（如果不存在）
    返回超级管理员的token用于免登录
    """
    from passlib.hash import pbkdf2_sha256

    async with AsyncSessionLocal() as session:
        # 检查超级管理员是否存在
        result = await session.execute(
            select(User).where(User.user_name == settings.SUPER_ADMIN_USERNAME)
        )
        admin = result.scalars().first()

        if admin:
            print(f"✅ 超级管理员已存在: {admin.user_name}")
            # 生成token
            token = create_access_token(data={"sub": str(admin.user_id)})
            print(f"🔑 超级管理员Token: {token}")
            return token

        # 创建超级管理员 - 使用PBKDF2哈希密码
        hashed_password = pbkdf2_sha256.hash(
            settings.SUPER_ADMIN_PASSWORD, rounds=100000
        )

        # 直接创建，user_type=1为超级管理员
        admin = User(
            user_name=settings.SUPER_ADMIN_USERNAME,
            email=settings.SUPER_ADMIN_EMAIL,
            full_name=settings.SUPER_ADMIN_FULL_NAME,
            hashed_password=hashed_password,
            user_type=1,  # 超级管理员
            is_active=True,
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print(f"✅ 超级管理员创建成功: {admin.user_name}")

        # 生成token
        token = create_access_token(data={"sub": str(admin.user_id)})
        print(f"🔑 超级管理员Token: {token}")
        return token


async def run_init_db():
    """
    供应用启动时调用的统一初始化函数
    """
    print("=" * 50)
    print("🛠️  正在执行数据库自动初始化...")
    try:
        await create_database_if_not_exists()
        await init_models()
        await create_super_admin()  # 新增：创建超级管理员
        print("✨ 数据库巡检与初始化任务执行成功！")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        # 这里可以选择抛出异常阻止启动，或者仅记录日志
        raise e
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_init_db())