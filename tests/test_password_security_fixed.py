import pytest
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService


class TestPasswordSecurityFixed:
    """密码安全测试类 - 修复版本"""

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
        password = "TestPass123!"
        hashed = user_service._hash_password(password)
        
        # 验证哈希不为空且以$2b$开头（bcrypt特征）
        assert hashed is not None
        assert hashed.startswith('$2b$')
        
        # 验证相同密码产生不同哈希（由于盐值）
        hashed2 = user_service._hash_password(password)
        assert hashed != hashed2

    def test_verify_password(self, user_service):
        """测试密码验证功能"""
        password = "TestPass123!"
        hashed = user_service._hash_password(password)
        
        # 验证正确密码
        assert user_service.verify_password(password, hashed) is True
        
        # 验证错误密码
        assert user_service.verify_password("WrongPass123!", hashed) is False

    def test_password_strength_validation_success(self, user_service):
        """测试密码强度验证 - 成功案例"""
        valid_passwords = [
            "StrongPass123!",
            "MyP@ssw0rd",
            "Complex$Pass2",
            "Secure@Pass1"
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
            ("password", "密码必须包含至少一个大写字母"),
            ("password123", "密码必须包含至少一个大写字母"),
            ("Password123", "密码必须包含至少一个特殊字符"),
            ("Password123!", "密码不能包含常见的弱密码模式")
        ]
        
        for password, expected_error in invalid_passwords:
            try:
                user_service._validate_password_strength(password)
                assert False, f"Expected exception for password: {password}"
            except Exception as e:
                assert expected_error in str(e)

    def test_weak_patterns_detection(self, user_service):
        """测试弱密码模式检测"""
        weak_passwords = [
            "12345678!",
            "password123!",
            "admin123!",
            "qwerty123!",
            "abc123!",
            "111111!",
            "000000!"
        ]
        
        for password in weak_passwords:
            try:
                user_service._validate_password_strength(password)
                assert False, f"Expected exception for weak password: {password}"
            except Exception as e:
                assert "密码不能包含常见的弱密码模式" in str(e)

    def test_password_length_limit(self, user_service):
        """测试密码长度限制（bcrypt 72字节限制）"""
        # 创建一个超过72字节的长密码
        long_password = "A" * 100 + "1!"
        
        # 应该不抛出异常（被截断）
        hashed = user_service._hash_password(long_password)
        assert hashed is not None
        assert hashed.startswith('$2b$')


class TestUserSchemaValidationFixed:
    """用户模式验证测试类 - 修复版本"""

    def test_valid_password_schema(self):
        """测试有效密码模式验证"""
        from app.schemas.user_schema import UserCreate
        
        valid_passwords = [
            "StrongPass123!",
            "MyP@ssw0rd",
            "Complex$Pass2",
            "Secure@Pass1"
        ]
        
        for password in valid_passwords:
            user_data = UserCreate(
                user_name="testuser",
                password=password,
                email="test@example.com"
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
            ("password123!", "密码不能包含常见的弱密码模式")
        ]
        
        for password, expected_error in invalid_passwords:
            try:
                UserCreate(
                    user_name="testuser",
                    password=password,
                    email="test@example.com"
                )
                assert False, f"Expected validation error for password: {password}"
            except ValidationError as e:
                assert expected_error in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])