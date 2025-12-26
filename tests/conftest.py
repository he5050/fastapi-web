import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import get_db
from app.main import app
from app.models.user_model import Base
from unittest.mock import AsyncMock
from faker import Faker

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

fake = Faker("zh_CN")


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session) -> Generator:
    """创建测试客户端"""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_user_data():
    """生成示例用户数据"""
    return {
        "user_name": fake.user_name(),
        "email": fake.email(),
        "password": "StrongPass123!",
        "full_name": fake.name(),
    }


@pytest.fixture
def sample_user_create():
    """生成UserCreate示例数据"""
    from app.schemas.user_schema import UserCreate
    return UserCreate(
        user_name=fake.user_name(),
        email=fake.email(),
        password="StrongPass123!",
        full_name=fake.name(),
    )


@pytest.fixture
def sample_user_update():
    """生成UserUpdate示例数据"""
    from app.schemas.user_schema import UserUpdate
    return UserUpdate(
        email=fake.email(),
        full_name=fake.name(),
    )


class UserFactory:
    """用户数据工厂"""
    
    @staticmethod
    def create_user_dict(**overrides):
        """创建用户字典数据"""
        data = {
            "user_name": fake.user_name(),
            "email": fake.email(),
            "password": "StrongPass123!",
            "full_name": fake.name(),
            "is_active": True,
            "is_deleted": False,
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def create_user_model(**overrides):
        """创建User模型实例"""
        from app.models.user_model import User
        from app.services.user_service import UserService
        
        # 创建哈希密码
        user_service = UserService(None)  # 不需要db实例来哈希密码
        password = overrides.get("password", "StrongPass123!")
        hashed_password = user_service._hash_password(password)
        
        data = UserFactory.create_user_dict(hashed_password=hashed_password, **overrides)
        data.pop("password")  # 移除明文密码
        
        return User(**data)


@pytest.fixture
def user_factory():
    """用户数据工厂fixture"""
    return UserFactory


@pytest.fixture
async def created_user(db_session, user_factory):
    """创建数据库中的测试用户"""
    user = user_factory.create_user_model()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def invalid_user_data():
    """生成无效用户数据用于测试"""
    return [
        {"user_name": "ab", "password": "StrongPass123!", "email": "test@example.com"},  # 用户名太短
        {"user_name": "testuser", "password": "weak", "email": "test@example.com"},  # 密码太弱
        {"user_name": "testuser", "password": "StrongPass123!", "email": "invalid-email"},  # 邮箱无效
        {"user_name": "", "password": "StrongPass123!", "email": "test@example.com"},  # 用户名空
        {"user_name": "testuser", "password": "", "email": "test@example.com"},  # 密码空
    ]


@pytest.fixture
def pagination_test_data():
    """分页测试数据"""
    return [
        {"page": 1, "page_size": 10, "expected_total_pages": 1},
        {"page": 2, "page_size": 5, "expected_total_pages": 2},
        {"page": 0, "page_size": 10, "expected_total_pages": 1},  # page边界测试
        {"page": 1, "page_size": 0, "expected_total_pages": 1},  # page_size边界测试
        {"page": 1, "page_size": 101, "expected_total_pages": 1},  # page_size超限测试
    ]
