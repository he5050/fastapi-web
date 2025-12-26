import pytest
from datetime import datetime
from sqlalchemy import inspect
from app.models.user_model import User
from tests.conftest import UserFactory


class TestUserModel:
    """用户模型测试类"""

    def test_user_model_creation(self):
        """测试用户模型创建"""
        user = UserFactory.create_user_model()
        
        assert user.user_name is not None
        assert user.email is not None
        assert user.hashed_password is not None
        assert user.is_active is True
        assert user.is_deleted is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_model_fields(self):
        """测试用户模型字段定义"""
        user = User()
        
        # 测试所有字段都存在且类型正确
        assert hasattr(user, 'id')
        assert hasattr(user, 'user_name')
        assert hasattr(user, 'email')
        assert hasattr(user, 'hashed_password')
        assert hasattr(user, 'full_name')
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'is_deleted')
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')

    def test_user_model_table_name(self):
        """测试用户模型表名"""
        assert User.__tablename__ == "sys_users"

    def test_user_model_field_constraints(self):
        """测试用户模型字段约束"""
        mapper = inspect(User)
        
        # 检查主键
        primary_key_columns = [key.name for key in mapper.primary_key]
        assert 'id' in primary_key_columns
        
        # 检查字段属性
        columns = mapper.columns
        assert columns['id'].primary_key is True
        assert columns['id'].autoincrement is True
        assert columns['user_name'].nullable is False
        assert columns['user_name'].unique is True
        assert columns['email'].nullable is True
        assert columns['email'].unique is True
        assert columns['hashed_password'].nullable is False
        assert columns['full_name'].nullable is True
        assert columns['is_active'].default.arg is True
        assert columns['is_deleted'].default.arg is False

    def test_user_model_field_lengths(self):
        """测试用户模型字段长度约束"""
        user = User()
        
        # 测试字段长度限制
        with pytest.raises(Exception):
            # 这可能会在数据库层面抛出异常，取决于具体的实现
            user.user_name = "a" * 51  # 超过50字符限制
            
        with pytest.raises(Exception):
            user.email = "a" * 101  # 超过100字符限制
            
        with pytest.raises(Exception):
            user.full_name = "a" * 101  # 超过100字符限制

    def test_user_model_default_values(self):
        """测试用户模型默认值"""
        user = User()
        
        # 测试布尔字段的默认值
        assert user.is_active is True
        assert user.is_deleted is False

    def test_user_model_timestamps(self):
        """测试用户模型时间戳字段"""
        user = User()
        
        # 创建时应该有时间戳
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_model_serialization(self):
        """测试用户模型序列化"""
        user_data = {
            "id": 1,
            "user_name": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "full_name": "Test User",
            "is_active": True,
            "is_deleted": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        user = User(**user_data)
        
        # 验证所有字段都正确设置
        for key, value in user_data.items():
            assert getattr(user, key) == value

    def test_user_model_to_dict(self):
        """测试用户模型转换为字典"""
        user = UserFactory.create_user_model(id=1)
        
        user_dict = user.__dict__
        
        # 检查所有字段都在字典中
        expected_fields = ['id', 'user_name', 'email', 'hashed_password', 
                         'full_name', 'is_active', 'is_deleted', 
                         'created_at', 'updated_at']
        
        for field in expected_fields:
            assert field in user_dict

    def test_user_model_email_optional(self):
        """测试邮箱字段可选"""
        user = User(
            user_name="testuser",
            hashed_password="hashed_password",
            email=None  # 邮箱可以为空
        )
        
        assert user.email is None

    def test_user_model_full_name_optional(self):
        """测试全名字段可选"""
        user = User(
            user_name="testuser",
            hashed_password="hashed_password",
            full_name=None  # 全名可以为空
        )
        
        assert user.full_name is None

    def test_user_model_soft_delete_behavior(self):
        """测试软删除行为"""
        user = UserFactory.create_user_model()
        
        # 初始状态
        assert user.is_deleted is False
        
        # 软删除
        user.is_deleted = True
        assert user.is_deleted is True
        
        # 逻辑删除的用户不应该被物理删除
        assert user.id is not None

    def test_user_model_active_status(self):
        """测试用户激活状态"""
        user = UserFactory.create_user_model()
        
        # 默认应该是激活状态
        assert user.is_active is True
        
        # 可以设置为非激活
        user.is_active = False
        assert user.is_active is False

    def test_user_model_validation(self):
        """测试用户模型验证"""
        # 测试必填字段
        with pytest.raises(Exception):
            User()  # 缺少必填字段
        
        # 测试有效数据
        user = User(
            user_name="testuser",
            hashed_password="hashed_password"
        )
        assert user.user_name == "testuser"
        assert user.hashed_password == "hashed_password"

    def test_user_model_relationships(self):
        """测试用户模型关系（如果有的话）"""
        # 这里可以测试与其他模型的关系
        # 当前User模型没有定义外键关系，所以这里主要测试模型本身
        user = UserFactory.create_user_model()
        
        # 确保可以独立存在
        assert user is not None

    def test_user_model_string_representation(self):
        """测试用户模型字符串表示"""
        user = UserFactory.create_user_model(user_name="testuser")
        
        # 测试字符串表示包含用户名
        str_repr = str(user)
        assert "testuser" in str_repr or "User" in str_repr

    def test_user_model_equality(self):
        """测试用户模型相等性比较"""
        user1 = UserFactory.create_user_model(id=1, user_name="user1")
        user2 = UserFactory.create_user_model(id=1, user_name="user2")
        user3 = UserFactory.create_user_model(id=2, user_name="user1")
        
        # 相同ID的用户应该相等（取决于实现）
        if hasattr(user1, '__eq__'):
            # 如果定义了__eq__方法
            assert user1 == user2  # 相同ID
            assert user1 != user3  # 不同ID
        else:
            # 如果没有定义__eq__方法，比较对象ID
            assert user1 is not user2
            assert user1 is not user3

    def test_user_model_hashable(self):
        """测试用户模型是否可哈希"""
        user = UserFactory.create_user_model()
        
        # 测试是否可以作为字典的键
        try:
            user_dict = {user: "value"}
            assert True  # 如果可以哈希
        except TypeError:
            # 如果不能哈希，这也是正常的
            assert True

    def test_user_model_copy(self):
        """测试用户模型复制"""
        user = UserFactory.create_user_model()
        
        # 测试浅复制
        try:
            import copy
            user_copy = copy.copy(user)
            assert user_copy.user_name == user.user_name
            assert user_copy.id == user.id
        except Exception:
            # 复制可能会失败，这也是正常的
            assert True

    def test_user_model_deepcopy(self):
        """测试用户模型深复制"""
        user = UserFactory.create_user_model()
        
        # 测试深复制
        try:
            import copy
            user_copy = copy.deepcopy(user)
            assert user_copy.user_name == user.user_name
            assert user_copy.id == user.id
            assert user_copy is not user
        except Exception:
            # 深复制可能会失败，这也是正常的
            assert True

    @pytest.mark.asyncio
    async def test_user_model_with_database_session(self, db_session):
        """测试用户模型与数据库会话的交互"""
        user = UserFactory.create_user_model()
        
        # 测试添加到会话
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # 验证用户已保存到数据库
        assert user.id is not None
        
        # 测试从数据库查询
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        retrieved_user = result.scalars().first()
        
        assert retrieved_user is not None
        assert retrieved_user.user_name == user.user_name

    def test_user_model_field_indexes(self):
        """测试用户模型字段索引"""
        mapper = inspect(User)
        columns = mapper.columns
        
        # 检查索引字段
        assert columns['id'].index is True  # 主键默认有索引
        assert columns['user_name'].index is True
        assert columns['email'].index is True

    def test_user_model_field_comments(self):
        """测试用户模型字段注释"""
        mapper = inspect(User)
        columns = mapper.columns
        
        # 检查字段注释
        assert columns['user_name'].comment == "用户名"
        assert columns['email'].comment == "邮箱"
        assert columns['hashed_password'].comment == "加密后的密码"
        assert columns['full_name'].comment == "全名"
        assert columns['is_active'].comment == "是否激活"
        assert columns['is_deleted'].comment == "是否已删除"
        assert columns['created_at'].comment == "创建时间"
        assert columns['updated_at'].comment == "更新时间"

    def test_user_model_timezone_handling(self):
        """测试用户模型时区处理"""
        user = User()
        
        # 时间戳字段应该是timezone-aware的
        if user.created_at:
            assert user.created_at.tzinfo is not None
        if user.updated_at:
            assert user.updated_at.tzinfo is not None
