import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate


class TestPasswordSecurity:
    """密码安全测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        mock_session = Mock(spec=AsyncSession)
        return mock_session

    @pytest.fixture
    def user_service(self, mock_db):
        """创建用户服务实例"""
        return UserService(mock_db)

    def test_hash_password_bcrypt(self, user_service):
        """测试密码哈希使用bcrypt"""
        password = "TestPassword123!"
        hashed = user_service._hash_password(password)

        # 验证哈希不为空
        assert hashed is not None
        assert len(hashed) > 50  # bcrypt哈希通常较长

        # 验证相同密码产生不同哈希（由于盐值）
        hashed2 = user_service._hash_password(password)
        assert hashed != hashed2

    def test_verify_password(self, user_service):
        """测试密码验证功能"""
        password = "TestPassword123!"
        hashed = user_service._hash_password(password)

        # 验证正确密码
        assert user_service.verify_password(password, hashed) is True

        # 验证错误密码
        assert user_service.verify_password("WrongPassword123!", hashed) is False

    def test_password_strength_validation_success(self, user_service):
        """测试密码强度验证 - 成功案例"""
        valid_passwords = [
            "StrongPass123!",
            "MyP@ssw0rd",
            "Secure#Password1",
            "Complex$Pass2",
        ]

        for password in valid_passwords:
            # 应该不抛出异常
            user_service._validate_password_strength(password)

    def test_password_strength_validation_failure(self, user_service):
        """测试密码强度验证 - 失败案例"""
        invalid_passwords = [
            ("short", "密码长度至少8位"),
            ("noUppercase1!", "密码必须包含至少一个大写字母"),
            ("NOLOWERCASE1!", "密码必须包含至少一个小写字母"),
            ("NoNumberPass!", "密码必须包含至少一个数字"),
            ("NoSpecialChar1", "密码必须包含至少一个特殊字符"),
            ("12345678", "密码必须包含至少一个大写字母"),
            ("Password", "密码必须包含至少一个数字"),
            ("password123", "密码必须包含至少一个大写字母"),
            ("Password123", "密码必须包含至少一个特殊字符"),
            ("Password123!", "密码不能包含常见的弱密码模式"),  # 包含"password"
        ]

        for password, expected_error in invalid_passwords:
            with pytest.raises(Exception) as exc_info:
                user_service._validate_password_strength(password)
            assert expected_error in str(exc_info.value)

    def test_weak_patterns_detection(self, user_service):
        """测试弱密码模式检测"""
        weak_passwords = [
            "My123456Password!",
            "SecureAdmin123!",
            "TestQwerty123!",
            "MyABC123Pass!",
            "My111111Pass!",
            "My000000Pass!",
        ]

        for password in weak_passwords:
            with pytest.raises(Exception) as exc_info:
                user_service._validate_password_strength(password)
            assert "密码不能包含常见的弱密码模式" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_with_password_validation(self, user_service, mock_db):
        """测试创建用户时的密码验证"""
        # 模拟repository方法
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.get_by_email = AsyncMock(return_value=None)
        user_service.repo.create = AsyncMock()

        # 测试有效密码
        valid_user_data = UserCreate(
            user_name="testuser", email="test@example.com", password="StrongPass123!"
        )

        # 应该不抛出异常
        await user_service.create_user(valid_user_data)

        # 测试无效密码
        invalid_user_data = UserCreate(
            user_name="testuser2", email="test2@example.com", password="weak"  # 弱密码
        )

        with pytest.raises(Exception) as exc_info:
            await user_service.create_user(invalid_user_data)
        assert "密码长度至少8位" in str(exc_info.value)


class TestUserSchemaValidation:
    """用户模式验证测试类"""

    def test_valid_password_schema(self):
        """测试有效密码模式验证"""
        from app.schemas.user_schema import UserCreate

        valid_passwords = ["StrongPass123!", "MyP@ssw0rd", "Secure#Password1"]

        for password in valid_passwords:
            user_data = UserCreate(
                user_name="testuser", password=password, email="test@example.com"
            )
            assert user_data.password == password

    def test_invalid_password_schema(self):
        """测试无效密码模式验证"""
        from app.schemas.user_schema import UserCreate
        from pydantic import ValidationError

        invalid_passwords = [
            ("short", "密码长度至少8位"),
            ("NoSpecialChar1", "密码必须包含至少一个特殊字符"),
            ("nouppercase1!", "密码必须包含至少一个大写字母"),
            ("NOLOWERCASE1!", "密码必须包含至少一个小写字母"),
            ("NoNumberPass!", "密码必须包含至少一个数字"),
        ]

        for password, expected_error in invalid_passwords:
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(
                    user_name="testuser", password=password, email="test@example.com"
                )
            assert expected_error in str(exc_info.value)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
