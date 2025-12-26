import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user_model import User
from app.core.exceptions import AppError
from tests.conftest import UserFactory


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

    @pytest.fixture
    def sample_user(self):
        """创建示例用户"""
        return UserFactory.create_user_model(id=1)

    @pytest.mark.asyncio
    async def test_get_user_existing(self, user_service, sample_user):
        """测试获取存在的用户"""
        user_service.repo.get_by_id = AsyncMock(return_value=sample_user)
        
        result = await user_service.get_user(1)
        
        assert result == sample_user
        user_service.repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service):
        """测试获取不存在的用户"""
        user_service.repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(AppError) as exc_info:
            await user_service.get_user(999)
        
        assert "用户 ID 999 不存在" in str(exc_info.value)
        user_service.repo.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_list_users_normal_case(self, user_service, sample_user):
        """测试正常分页查询用户列表"""
        mock_response = {
            "records": [sample_user],
            "total": 1,
            "page": 1,
            "page_size": 10,
            "total_page": 1
        }
        user_service.repo.get_list = AsyncMock(return_value=([sample_user], 1))
        
        result = await user_service.list_users(1, 10)
        
        assert result["records"] == [sample_user]
        assert result["total"] == 1
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_page"] == 1

    @pytest.mark.asyncio
    async def test_list_users_edge_cases(self, user_service):
        """测试用户列表分页边界条件"""
        test_cases = [
            {"page": 1, "page_size": 1, "expected_total_page": 1},
            {"page": 2, "page_size": 5, "expected_total_page": 1},
            {"page": 1, "page_size": 100, "expected_total_page": 1},
        ]
        
        for case in test_cases:
            user_service.repo.get_list = AsyncMock(return_value=([], 0))
            
            result = await user_service.list_users(case["page"], case["page_size"])
            
            assert result["page"] == case["page"]
            assert result["page_size"] == case["page_size"]
            assert result["total_page"] == case["expected_total_page"]

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, sample_user):
        """测试成功创建用户"""
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.get_by_email = AsyncMock(return_value=None)
        user_service.repo.create = AsyncMock(return_value=sample_user)
        
        user_data = UserCreate(
            user_name="testuser",
            email="test@example.com",
            password="StrongPass123!"
        )
        
        result = await user_service.create_user(user_data)
        
        assert result == sample_user
        user_service.repo.get_by_user_name.assert_called_once_with("testuser")
        user_service.repo.get_by_email.assert_called_once_with("test@example.com")
        user_service.repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service, sample_user):
        """测试创建用户时用户名重复"""
        user_service.repo.get_by_user_name = AsyncMock(return_value=sample_user)
        
        user_data = UserCreate(
            user_name="existinguser",
            email="test@example.com",
            password="StrongPass123!"
        )
        
        with pytest.raises(AppError) as exc_info:
            await user_service.create_user(user_data)
        
        assert "用户名 existinguser 已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, sample_user):
        """测试创建用户时邮箱重复"""
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.get_by_email = AsyncMock(return_value=sample_user)
        
        user_data = UserCreate(
            user_name="newuser",
            email="existing@example.com",
            password="StrongPass123!"
        )
        
        with pytest.raises(AppError) as exc_info:
            await user_service.create_user(user_data)
        
        assert "邮箱 existing@example.com 已被注册" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_without_email(self, user_service, sample_user):
        """测试创建用户时不提供邮箱"""
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.create = AsyncMock(return_value=sample_user)
        
        user_data = UserCreate(
            user_name="testuser",
            email=None,
            password="StrongPass123!"
        )
        
        result = await user_service.create_user(user_data)
        
        assert result == sample_user
        user_service.repo.get_by_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, sample_user):
        """测试成功更新用户"""
        user_service.repo.get_by_id = AsyncMock(return_value=sample_user)
        user_service.repo.update = AsyncMock(return_value=sample_user)
        
        update_data = UserUpdate(
            email="new@example.com",
            full_name="New Name"
        )
        
        result = await user_service.update_user(1, update_data)
        
        assert result == sample_user
        user_service.repo.get_by_id.assert_called_once_with(1)
        user_service.repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service):
        """测试更新不存在的用户"""
        user_service.repo.get_by_id = AsyncMock(return_value=None)
        
        update_data = UserUpdate(full_name="New Name")
        
        with pytest.raises(AppError) as exc_info:
            await user_service.update_user(999, update_data)
        
        assert "用户 ID 999 不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_user_partial_update(self, user_service, sample_user):
        """测试用户部分更新"""
        user_service.repo.get_by_id = AsyncMock(return_value=sample_user)
        user_service.repo.update = AsyncMock(return_value=sample_user)
        
        # 只更新邮箱
        update_data = UserUpdate(email="new@example.com")
        
        result = await user_service.update_user(1, update_data)
        
        assert result == sample_user
        # 验证只传递了email字段
        call_args = user_service.repo.update.call_args[0]
        assert call_args[1] == {"email": "new@example.com"}

    @pytest.mark.asyncio
    async def test_update_user_no_changes(self, user_service, sample_user):
        """测试用户无更新"""
        user_service.repo.get_by_id = AsyncMock(return_value=sample_user)
        user_service.repo.update = AsyncMock(return_value=sample_user)
        
        # 空更新数据
        update_data = UserUpdate()
        
        result = await user_service.update_user(1, update_data)
        
        assert result == sample_user
        # 验证传递了空字典
        call_args = user_service.repo.update.call_args[0]
        assert call_args[1] == {}

    @pytest.mark.asyncio
    async def test_update_user_failure(self, user_service, sample_user):
        """测试用户更新失败"""
        user_service.repo.get_by_id = AsyncMock(return_value=sample_user)
        user_service.repo.update = AsyncMock(return_value=None)
        
        update_data = UserUpdate(full_name="New Name")
        
        with pytest.raises(AppError) as exc_info:
            await user_service.update_user(1, update_data)
        
        assert "用户 ID 1 更新失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service):
        """测试成功删除用户"""
        user_service.repo.get_by_id = AsyncMock(return_value=Mock())
        user_service.repo.delete = AsyncMock(return_value=True)
        
        result = await user_service.delete_user(1)
        
        assert result is True
        user_service.repo.get_by_id.assert_called_once_with(1)
        user_service.repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service):
        """测试删除不存在的用户"""
        user_service.repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(AppError) as exc_info:
            await user_service.delete_user(999)
        
        assert "用户 ID 999 不存在" in str(exc_info.value)
        user_service.repo.get_by_id.assert_called_once_with(999)
        user_service.repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user_soft_delete_confirmation(self, user_service):
        """测试用户软删除确认"""
        mock_user = Mock()
        user_service.repo.get_by_id = AsyncMock(return_value=mock_user)
        user_service.repo.delete = AsyncMock(return_value=True)
        
        result = await user_service.delete_user(1)
        
        assert result is True
        # 确保先验证用户存在，再执行删除
        user_service.repo.get_by_id.assert_called_once_with(1)
        user_service.repo.delete.assert_called_once_with(1)

    def test_password_hashing_with_long_password(self, user_service):
        """测试长密码哈希（bcrypt 72字节限制）"""
        # 创建超过72字节的密码
        long_password = "A" * 100 + "1!"
        
        hashed = user_service._hash_password(long_password)
        
        assert hashed is not None
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_password_verification_with_long_password(self, user_service):
        """测试长密码验证"""
        long_password = "A" * 100 + "1!"
        hashed = user_service._hash_password(long_password)
        
        # 验证长密码
        assert user_service.verify_password(long_password, hashed) is True
        # 验证错误密码
        assert user_service.verify_password("Wrong" + "A" * 100 + "1!", hashed) is False

    def test_password_validation_edge_cases(self, user_service):
        """测试密码验证边界情况"""
        # 测试刚好8位密码
        try:
            user_service._validate_password_strength("Abcdef1!")
            # 应该通过，刚好8位
        except AppError:
            pytest.fail("8位密码应该通过验证")
        
        # 测试包含各种特殊字符
        special_chars = ["!@#$%^&*()", "?{}|<>", "[];':\"", "./<>?"]
        for special in special_chars:
            try:
                user_service._validate_password_strength(f"Abcdef1{special}")
            except AppError:
                pytest.fail(f"包含特殊字符 {special} 的密码应该通过验证")

    def test_password_validation_weak_patterns(self, user_service):
        """测试密码弱模式检测"""
        weak_passwords = [
            "Password123!",
            "Admin12345!",
            "Qwerty123!",
            "12345678!",
            "Abc12345!",
            "Password!123",
        ]
        
        for password in weak_passwords:
            with pytest.raises(AppError) as exc_info:
                user_service._validate_password_strength(password)
            assert "密码不能包含常见的弱密码模式" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, user_service):
        """测试并发用户创建"""
        import asyncio
        
        # 模拟repository方法
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.get_by_email = AsyncMock(return_value=None)
        user_service.repo.create = AsyncMock(return_value=Mock())
        
        async def create_user_task(user_name):
            user_data = UserCreate(
                user_name=user_name,
                email=f"{user_name}@example.com",
                password="StrongPass123!"
            )
            return await user_service.create_user(user_data)
        
        # 并发创建用户
        tasks = [create_user_task(f"user{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_create_failure(self, user_service):
        """测试创建用户失败时事务回滚"""
        user_service.repo.get_by_user_name = AsyncMock(return_value=None)
        user_service.repo.get_by_email = AsyncMock(return_value=None)
        user_service.repo.create = AsyncMock(side_effect=Exception("Database error"))
        
        user_data = UserCreate(
            user_name="testuser",
            email="test@example.com",
            password="StrongPass123!"
        )
        
        with pytest.raises(Exception, match="Database error"):
            await user_service.create_user(user_data)

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """测试服务初始化"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        with patch('app.services.user_service.UserRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            
            service = UserService(mock_db)
            
            assert service.repo == mock_repo
            mock_repo_class.assert_called_once_with(mock_db)

    def test_service_methods_exist(self, user_service):
        """测试服务方法存在"""
        assert hasattr(user_service, 'get_user')
        assert hasattr(user_service, 'list_users')
        assert hasattr(user_service, 'create_user')
        assert hasattr(user_service, 'update_user')
        assert hasattr(user_service, 'delete_user')
        assert hasattr(user_service, '_hash_password')
        assert hasattr(user_service, 'verify_password')
        assert hasattr(user_service, '_validate_password_strength')

    @pytest.mark.asyncio
    async def test_list_users_empty_result(self, user_service):
        """测试空用户列表"""
        user_service.repo.get_list = AsyncMock(return_value=([], 0))
        
        result = await user_service.list_users(1, 10)
        
        assert result["records"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_page"] == 0

    @pytest.mark.asyncio
    async def test_list_users_large_page_size(self, user_service, sample_user):
        """测试大分页大小"""
        user_service.repo.get_list = AsyncMock(return_value=([sample_user], 1))
        
        result = await user_service.list_users(1, 1000)
        
        assert result["page_size"] == 1000
        assert result["total_page"] == 1

    @pytest.mark.asyncio
    async def test_update_user_with_none_values(self, user_service, sample_user):
        """测试更新用户时包含None值"""
        user_service.repo.get_by_id = AsyncMock(return_value=sample_user)
        user_service.repo.update = AsyncMock(return_value=sample_user)
        
        # 更新数据包含None值
        update_data = UserUpdate(email=None, full_name="New Name")
        
        result = await user_service.update_user(1, update_data)
        
        assert result == sample_user
        # 验证None值被正确处理
        call_args = user_service.repo.update.call_args[0]
        assert call_args[1]["full_name"] == "New Name"

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
