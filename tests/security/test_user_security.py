"""
用户安全权限测试用例
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.security import create_access_token, verify_password
from app.models.user_model import User
from app.services.user_service import UserService

client = TestClient(app)


@pytest.fixture
async def admin_user():
    """创建测试管理员用户"""
    return User(
        user_id=1,
        user_name="admin",
        email="admin@test.com",
        hashed_password="$2b$12$test_hash",
        full_name="系统管理员",
        is_active=True,
        user_type=1,
        is_deleted=False
    )


@pytest.fixture
async def normal_user():
    """创建测试普通用户"""
    return User(
        user_id=2,
        user_name="normaluser",
        email="user@test.com",
        hashed_password="$2b$12$test_hash",
        full_name="普通用户",
        is_active=True,
        user_type=9,
        is_deleted=False
    )


@pytest.fixture
async def another_user():
    """创建另一个测试普通用户"""
    return User(
        user_id=3,
        user_name="anotheruser",
        email="another@test.com",
        hashed_password="$2b$12$test_hash",
        full_name="另一个用户",
        is_active=True,
        user_type=9,
        is_deleted=False
    )


class TestUserSecurity:
    """用户安全权限测试类"""

    def test_admin_cannot_delete_themselves(self, admin_user):
        """测试管理员不能删除自己"""
        service = UserService(None)
        
        # 管理员尝试删除自己应该抛出异常
        with pytest.raises(Exception) as exc_info:
            # 这里需要模拟数据库操作，实际测试中需要真实的db session
            pass
        
        # 验证异常消息
        assert "不能删除自己的账户" in str(exc_info.value)

    def test_normal_user_cannot_delete_users(self, normal_user, admin_user):
        """测试普通用户不能删除任何用户"""
        service = UserService(None)
        
        # 普通用户尝试删除管理员应该返回False
        result = service.can_delete_user(normal_user, admin_user.user_id)
        assert result is False

    def test_normal_user_can_only_view_themselves(self, normal_user, another_user):
        """测试普通用户只能查看自己"""
        service = UserService(None)
        
        # 普通用户可以查看自己
        assert service.can_view_user(normal_user, normal_user.user_id) is True
        
        # 普通用户不能查看其他用户
        assert service.can_view_user(normal_user, another_user.user_id) is False

    def test_admin_can_view_all_users(self, admin_user, normal_user, another_user):
        """测试管理员可以查看所有用户"""
        service = UserService(None)
        
        # 管理员可以查看所有用户
        assert service.can_view_user(admin_user, admin_user.user_id) is True
        assert service.can_view_user(admin_user, normal_user.user_id) is True
        assert service.can_view_user(admin_user, another_user.user_id) is True

    def test_normal_user_can_only_update_themselves(self, normal_user, another_user):
        """测试普通用户只能更新自己"""
        service = UserService(None)
        
        # 普通用户可以更新自己
        assert service.can_update_user(normal_user, normal_user.user_id) is True
        
        # 普通用户不能更新其他用户
        assert service.can_update_user(normal_user, another_user.user_id) is False

    def test_admin_cannot_update_other_admins(self, admin_user):
        """测试管理员不能更新其他管理员（模拟）"""
        service = UserService(None)
        
        # 这里需要模拟另一个管理员
        # 管理员尝试更新其他管理员应该抛出异常
        pass

    def test_user_output_permission_filtering(self, admin_user, normal_user):
        """测试用户输出权限过滤"""
        from app.schemas.user_schema import UserOut
        
        # 管理员查看管理员信息（应该显示完整信息）
        admin_output = UserOut.from_user_with_permission(admin_user, admin_user)
        assert admin_output.user_type == 1
        assert admin_output.email == "admin@test.com"
        assert admin_output.full_name == "系统管理员"
        
        # 普通用户查看管理员信息（应该隐藏敏感信息）
        admin_output_for_normal = UserOut.from_user_with_permission(admin_user, normal_user)
        assert admin_output_for_normal.user_type == 9  # 伪装成普通用户
        assert admin_output_for_normal.email is None
        assert admin_output_for_normal.full_name == "系统管理员"
        
        # 普通用户查看自己（应该显示部分信息，但隐藏用户类型）
        normal_output_self = UserOut.from_user_with_permission(normal_user, normal_user)
        assert normal_output_self.user_type == 9  # 对自己也隐藏真实用户类型
        assert normal_output_self.email == "user@test.com"
        assert normal_output_self.full_name == "普通用户"
        
        # 普通用户查看其他普通用户（应该隐藏邮箱）
        normal_output_other = UserOut.from_user_with_permission(normal_user, another_user=None)
        # 由于没有current_user，应该隐藏敏感信息
        pass

    def test_safe_user_output_method(self, admin_user, normal_user):
        """测试安全用户输出方法"""
        from app.schemas.user_schema import UserOut
        
        # 管理员查看所有信息
        admin_safe = UserOut.create_safe_user_output(admin_user, admin_user)
        assert admin_safe['user_type'] == 1
        assert admin_safe['email'] == "admin@test.com"
        
        # 普通用户查看自己
        normal_self = UserOut.create_safe_user_output(normal_user, normal_user)
        assert normal_self['user_type'] == 9  # 隐藏真实用户类型
        assert normal_self['email'] == "user@test.com"
        
        # 普通用户查看管理员
        normal_view_admin = UserOut.create_safe_user_output(admin_user, normal_user)
        assert normal_view_admin['user_type'] == 9  # 伪装成普通用户
        assert normal_view_admin['email'] is None
        assert normal_view_admin['full_name'] == "系统管理员"


@pytest.mark.asyncio
async def test_user_list_filtering():
    """测试用户列表权限过滤"""
    # 这个测试需要真实的数据库连接
    # 测试普通用户获取列表时应该过滤掉管理员
    pass


@pytest.mark.asyncio
async def test_api_endpoint_permissions():
    """测试API端点权限控制"""
    # 创建测试token
    admin_token = create_access_token(data={"sub": "1"})  # 管理员ID
    normal_token = create_access_token(data={"sub": "2"})  # 普通用户ID
    
    # 测试删除用户接口
    # 普通用户尝试删除管理员
    headers = {"Authorization": f"Bearer {normal_token}"}
    response = client.delete("/users/delete/1", headers=headers)
    assert response.status_code == 200
    assert "没有权限删除该用户" in response.json()["message"]
    
    # 测试查看用户详情接口
    # 普通用户尝试查看其他用户详情
    response = client.get("/users/detail/3", headers=headers)
    assert response.status_code == 200
    assert "没有权限查看该用户信息" in response.json()["message"]
    
    # 测试更新用户接口
    # 普通用户尝试更新其他用户
    update_data = {"full_name": "新名称"}
    response = client.put("/users/update/3", json=update_data, headers=headers)
    assert response.status_code == 200
    assert "没有权限修改该用户信息" in response.json()["message"]


class TestPermissionDecorators:
    """权限装饰器测试"""
    
    def test_require_admin_decorator(self):
        """测试管理员权限装饰器"""
        from app.core.permissions import require_admin
        from app.core.exceptions import AppError
        
        @require_admin
        async def test_function(current_user=None):
            return "success"
        
        # 管理用户应该通过
        admin_user = User(user_type=1)
        # 注意：这里的测试需要异步执行
        pass
        
        # 普通用户应该抛出异常
        normal_user = User(user_type=9)
        # 注意：这里的测试需要异步执行
        pass

    def test_require_self_or_admin_decorator(self):
        """测试本人或管理员权限装饰器"""
        from app.core.permissions import require_self_or_admin
        
        @require_self_or_admin
        async def test_function(user_id=None, current_user=None):
            return "success"
        
        # 管理员操作任何用户都应该通过
        admin_user = User(user_id=1, user_type=1)
        # 注意：这里的测试需要异步执行
        pass
        
        # 普通用户操作自己应该通过
        normal_user = User(user_id=2, user_type=9)
        # 注意：这里的测试需要异步执行
        pass
        
        # 普通用户操作其他人应该失败
        # 注意：这里的测试需要异步执行
        pass


if __name__ == "__main__":
    pytest.main([__file__])
