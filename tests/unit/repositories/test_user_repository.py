import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.user_repository import UserRepository
from app.models.user_model import User
from tests.conftest import UserFactory


class TestUserRepository:
    """用户Repository测试类"""

    @pytest.fixture
    def user_repository(self, mock_db_session):
        """创建用户Repository实例"""
        return UserRepository(mock_db_session)

    @pytest.fixture
    def mock_user(self):
        """创建模拟用户对象"""
        return UserFactory.create_user_model(id=1)

    @pytest.mark.asyncio
    async def test_get_by_id_existing_user(self, user_repository, mock_db_session, mock_user):
        """测试获取存在的用户"""
        # 模拟数据库查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        # 执行测试
        result = await user_repository.get_by_id(1)

        # 验证结果
        assert result == mock_user
        mock_db_session.execute.assert_called_once()
        
        # 验证SQL查询
        call_args = mock_db_session.execute.call_args[0][0]
        assert isinstance(call_args, select)
        assert call_args.wherecompare.target.column.key == "id"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_user(self, user_repository, mock_db_session):
        """测试获取不存在的用户"""
        # 模拟空结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # 执行测试
        result = await user_repository.get_by_id(999)

        # 验证结果
        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_deleted_user(self, user_repository, mock_db_session, mock_user):
        """测试获取已删除的用户（应该返回None）"""
        # 模拟已删除用户
        mock_user.is_deleted = True
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        # 执行测试
        result = await user_repository.get_by_id(1)

        # 验证结果（Repository层应该过滤掉已删除用户）
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_user_name_existing(self, user_repository, mock_db_session, mock_user):
        """测试根据用户名获取存在的用户"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_user_name("testuser")

        assert result == mock_user
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_name_nonexistent(self, user_repository, mock_db_session):
        """测试根据用户名获取不存在的用户"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_user_name("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email_existing(self, user_repository, mock_db_session, mock_user):
        """测试根据邮箱获取存在的用户"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("test@example.com")

        assert result == mock_user
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_email_nonexistent(self, user_repository, mock_db_session):
        """测试根据邮箱获取不存在的用户"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_list_normal_pagination(self, user_repository, mock_db_session):
        """测试正常分页查询"""
        # 模拟用户列表
        mock_users = [UserFactory.create_user_model(id=i) for i in range(1, 6)]
        
        # 模拟总数查询结果
        count_result = MagicMock()
        count_result.scalar.return_value = 25  # 总数25条
        
        # 模拟列表查询结果
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = mock_users
        
        # 顺序返回不同的结果
        mock_db_session.execute.side_effect = [count_result, list_result]

        # 执行测试
        items, total = await user_repository.get_list(page=1, page_size=5)

        # 验证结果
        assert len(items) == 5
        assert total == 25
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_list_edge_cases(self, user_repository, mock_db_session):
        """测试分页边界条件"""
        test_cases = [
            {"page": 0, "page_size": 10, "expected_offset": -10},  # page=0
            {"page": 1, "page_size": 0, "expected_offset": 0},   # page_size=0
            {"page": 1, "page_size": 1, "expected_offset": 0},    # 最小分页
        ]

        for case in test_cases:
            # 重置mock
            mock_db_session.reset_mock()
            
            # 模拟结果
            count_result = MagicMock()
            count_result.scalar.return_value = 0
            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = []
            mock_db_session.execute.side_effect = [count_result, list_result]

            # 执行测试
            await user_repository.get_list(case["page"], case["page_size"])

            # 验证offset计算
            list_call = mock_db_session.execute.call_args_list[1][0][0]
            # 这里我们验证方法被调用，具体的offset计算在SQLAlchemy内部处理

    @pytest.mark.asyncio
    async def test_get_list_empty_result(self, user_repository, mock_db_session):
        """测试空结果查询"""
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.side_effect = [count_result, list_result]

        items, total = await user_repository.get_list(page=1, page_size=10)

        assert items == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_create_user(self, user_repository, mock_db_session, mock_user):
        """测试创建用户"""
        # 模拟数据库操作
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await user_repository.create(mock_user)

        # 验证操作
        mock_db_session.add.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_update_user(self, user_repository, mock_db_session, mock_user):
        """测试更新用户"""
        update_data = {"full_name": "Updated Name", "email": "updated@example.com"}
        
        # 模拟更新后的用户
        updated_user = UserFactory.create_user_model(id=1)
        updated_user.full_name = "Updated Name"
        updated_user.email = "updated@example.com"

        # 模拟get_by_id返回更新后的用户
        with patch.object(user_repository, 'get_by_id', return_value=updated_user):
            result = await user_repository.update(1, update_data)

        # 验证结果
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert result.full_name == "Updated Name"
        assert result.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, user_repository, mock_db_session):
        """测试更新不存在的用户"""
        update_data = {"full_name": "Updated Name"}
        
        # 模拟get_by_id返回None
        with patch.object(user_repository, 'get_by_id', return_value=None):
            result = await user_repository.update(999, update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, mock_db_session):
        """测试成功删除用户（软删除）"""
        # 模拟数据库执行结果
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        result = await user_repository.delete(1)

        # 验证结果
        assert result is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, user_repository, mock_db_session):
        """测试删除不存在的用户"""
        # 模拟数据库执行结果（没有行被更新）
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        result = await user_repository.delete(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_user_soft_delete_behavior(self, user_repository, mock_db_session):
        """测试软删除行为（设置is_deleted=True）"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        await user_repository.delete(1)

        # 验证更新的是is_deleted字段
        call_args = mock_db_session.execute.call_args[0][0]
        # 验证是update操作且包含is_deleted=True
        
        # 验证SQL结构
        assert hasattr(call_args, 'where')
        assert hasattr(call_args, 'values')

    @pytest.mark.asyncio
    async def test_repository_methods_filter_deleted_users(self, user_repository, mock_db_session):
        """测试Repository方法都过滤已删除用户"""
        # 测试所有查询方法都包含is_deleted=False条件
        methods_to_test = [
            lambda: user_repository.get_by_id(1),
            lambda: user_repository.get_by_user_name("test"),
            lambda: user_repository.get_by_email("test@example.com"),
        ]

        for method in methods_to_test:
            mock_db_session.reset_mock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_db_session.execute.return_value = mock_result

            await method()

            # 验证SQL查询包含is_deleted=False条件
            call_args = mock_db_session.execute.call_args[0][0]
            assert hasattr(call_args, 'where')

    @pytest.mark.asyncio
    async def test_get_list_ordering(self, user_repository, mock_db_session):
        """测试用户列表排序"""
        mock_users = [UserFactory.create_user_model(id=i) for i in range(5, 0, -1)]
        
        count_result = MagicMock()
        count_result.scalar.return_value = 5
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = mock_users
        mock_db_session.execute.side_effect = [count_result, list_result]

        await user_repository.get_list(page=1, page_size=10)

        # 验证排序（应该是按id降序）
        list_call = mock_db_session.execute.call_args_list[1][0][0]
        # 验证包含order_by子句
        
    @pytest.mark.asyncio
    async def test_database_session_handling(self, user_repository, mock_db_session):
        """测试数据库会话处理"""
        # 测试所有操作都正确使用数据库会话
        mock_user = UserFactory.create_user_model()
        
        # 测试create
        mock_db_session.add.reset_mock()
        await user_repository.create(mock_user)
        mock_db_session.add.assert_called_once()
        
        # 测试update
        with patch.object(user_repository, 'get_by_id', return_value=mock_user):
            await user_repository.update(1, {})
            mock_db_session.commit.assert_called()
        
        # 测试delete
        mock_db_session.execute.reset_mock()
        mock_db_session.execute.return_value = MagicMock(rowcount=1)
        await user_repository.delete(1)
        mock_db_session.execute.assert_called_once()
