import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate
from app.core.exceptions import AppError


class TestUserService:
    """用户服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        mock_session = Mock(spec=AsyncSession)
        return mock_session

    @pytest.fixture
    def user_service(self, mock_db):
        """创建用户服务实例"""
        return UserService(mock_db)

    @pytest.mark.asyncio
    async def test_create_user_with_password_validation(self, user_service, mock_db):
        """测试创建用户时的密码验证"""
        # 模拟repository方法
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.get_by_email = AsyncMock(return_value=None)
        user_service.repo.create = AsyncMock(return_value=Mock())

        # 测试有效密码
        valid_user_data = UserCreate(
            user_name="testuser", email="test@example.com", password="StrongPass123!"
        )

        # 应该成功创建用户
        result = await user_service.create_user(valid_user_data)
        assert result is not None  # 验证创建成功

        # 测试服务内部的密码强度验证
        with pytest.raises(AppError) as exc_info:
            user_service._validate_password_strength("short1!")
        assert "密码长度至少8位" in str(exc_info.value)

    def test_basic_password_hashing(self, user_service):
        """测试基本密码哈希功能"""
        password = "TestPass123!"
        hashed = user_service._hash_password(password)

        assert hashed is not None
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_basic_password_verification(self, user_service):
        """测试基本密码验证功能"""
        password = "TestPass123!"
        hashed = user_service._hash_password(password)

        # 测试正确密码
        assert user_service.verify_password(password, hashed) is True

        # 测试错误密码
        assert user_service.verify_password("WrongPass!", hashed) is False

    def test_password_strength_basic(self, user_service):
        """测试基本密码强度验证"""
        # 测试有效密码
        try:
            user_service._validate_password_strength("StrongPass123!")
            # 如果没有抛出异常，测试通过
        except Exception:
            pytest.fail("Valid password should not raise exception")

        # 测试无效密码
        with pytest.raises(Exception):
            user_service._validate_password_strength("weak")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
