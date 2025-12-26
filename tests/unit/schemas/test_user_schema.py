import pytest
from pydantic import ValidationError
from app.schemas.user_schema import UserCreate


class TestUserSchemaValidation:
    """用户模式验证测试类"""

    def test_valid_user_creation(self):
        """测试有效用户创建"""
        user_data = UserCreate(
            user_name="testuser", password="StrongPass123!", email="test@example.com"
        )
        assert user_data.user_name == "testuser"
        assert user_data.password == "StrongPass123!"
        assert user_data.email == "test@example.com"

    def test_valid_password_schema(self):
        """测试有效密码模式验证"""
        valid_passwords = [
            "StrongPass123!",
            "MyP@ssw0rd",
            "Complex$Pass2",
            "Secure@Pass1",
        ]

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
            ("Password123!", "密码不能包含常见的弱密码模式"),
        ]

        for password, expected_error in invalid_passwords:
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(
                    user_name="testuser", password=password, email="test@example.com"
                )
            assert expected_error in str(exc_info.value)

    def test_invalid_email_format(self):
        """测试无效邮箱格式"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                user_name="testuser", password="StrongPass123!", email="invalid-email"
            )
        # Pydantic的邮箱验证有特定的错误消息，检查包含验证错误
        assert "email" in str(exc_info.value).lower()
        assert "not a valid email address" in str(exc_info.value).lower()

    def test_username_validation(self):
        """测试用户名验证"""
        # 测试过短用户名
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                user_name="ab", password="StrongPass123!", email="test@example.com"
            )
        assert "用户名长度不能少于 3 个字符" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
