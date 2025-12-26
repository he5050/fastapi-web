import pytest
from unittest.mock import Mock
from app.services.user_service import UserService


def test_basic_password_hashing():
    """测试基本密码哈希功能"""
    mock_db = Mock()
    service = UserService(mock_db)
    
    # 测试密码哈希
    password = "TestPass123!"
    hashed = service._hash_password(password)
    
    assert hashed is not None
    assert hashed.startswith('$2b$')
    assert len(hashed) > 50


def test_basic_password_verification():
    """测试基本密码验证功能"""
    mock_db = Mock()
    service = UserService(mock_db)
    
    password = "TestPass123!"
    hashed = service._hash_password(password)
    
    # 测试正确密码
    assert service.verify_password(password, hashed) is True
    
    # 测试错误密码
    assert service.verify_password("WrongPass!", hashed) is False


def test_password_strength_basic():
    """测试基本密码强度验证"""
    mock_db = Mock()
    service = UserService(mock_db)
    
    # 测试有效密码
    try:
        service._validate_password_strength("StrongPass123!")
        # 如果没有抛出异常，测试通过
    except Exception:
        pytest.fail("Valid password should not raise exception")
    
    # 测试无效密码
    with pytest.raises(Exception):
        service._validate_password_strength("weak")


def test_user_schema_basic():
    """测试基本用户模式验证"""
    from app.schemas.user_schema import UserCreate
    
    # 测试有效用户创建
    try:
        user = UserCreate(
            user_name="testuser",
            password="StrongPass123!",
            email="test@example.com"
        )
        assert user.user_name == "testuser"
    except Exception:
        pytest.fail("Valid user data should not raise exception")
    
    # 测试无效密码
    with pytest.raises(Exception):
        UserCreate(
            user_name="testuser",
            password="weak",
            email="test@example.com"
        )


if __name__ == "__main__":
    test_basic_password_hashing()
    test_basic_password_verification()
    test_password_strength_basic()
    test_user_schema_basic()
    print("所有基本功能测试通过！")