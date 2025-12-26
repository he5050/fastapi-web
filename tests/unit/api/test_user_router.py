import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app
from app.schemas.user_schema import UserCreate, UserUpdate, UserOut
from tests.conftest import UserFactory


class TestUserRouter:
    """用户路由测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "env" in response.json()

    def test_api_docs_availability(self, client):
        """测试API文档可用性"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_availability(self, client):
        """测试ReDoc文档可用性"""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestUserEndpoints:
    """用户端点测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            "user_name": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123!",
            "full_name": "Test User"
        }

    @pytest.fixture
    def mock_user(self):
        """模拟用户对象"""
        return UserFactory.create_user_model(id=1)

    def test_create_user_success(self, client, sample_user_data, mock_user):
        """测试成功创建用户"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_user.return_value = mock_user
            mock_service_class.return_value = mock_service
            
            response = client.post("/users/add", json=sample_user_data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"] is not None
            assert response_data["message"] == "成功"

    def test_create_user_invalid_data(self, client):
        """测试创建用户时数据无效"""
        invalid_data = {
            "user_name": "ab",  # 太短
            "email": "invalid-email",  # 无效邮箱
            "password": "weak",  # 弱密码
        }
        
        response = client.post("/users/add", json=invalid_data)
        
        # 应该返回422状态码（验证错误）
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["success"] is False
        assert "参数错误" in response_data["message"]

    def test_create_user_missing_required_fields(self, client):
        """测试创建用户时缺少必填字段"""
        incomplete_data = {
            "user_name": "testuser"
            # 缺少password
        }
        
        response = client.post("/users/add", json=incomplete_data)
        
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["success"] is False

    def test_create_user_duplicate_username(self, client, sample_user_data):
        """测试创建用户时用户名重复"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            from app.core.exceptions import AppError
            
            mock_service = AsyncMock()
            mock_service.create_user.side_effect = AppError("用户名 testuser 已存在")
            mock_service_class.return_value = mock_service
            
            response = client.post("/users/add", json=sample_user_data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is False
            assert "用户名 testuser 已存在" in response_data["message"]

    def test_create_user_duplicate_email(self, client, sample_user_data):
        """测试创建用户时邮箱重复"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            from app.core.exceptions import AppError
            
            mock_service = AsyncMock()
            mock_service.create_user.side_effect = AppError("邮箱 test@example.com 已被注册")
            mock_service_class.return_value = mock_service
            
            response = client.post("/users/add", json=sample_user_data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is False
            assert "邮箱 test@example.com 已被注册" in response_data["message"]

    def test_get_user_list_success(self, client, mock_user):
        """测试成功获取用户列表"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.list_users.return_value = {
                "records": [mock_user],
                "total": 1,
                "page": 1,
                "page_size": 10,
                "total_page": 1
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/users/list?page=1&pageSize=10")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["records"] is not None
            assert response_data["data"]["total"] == 1
            assert response_data["data"]["page"] == 1
            assert response_data["data"]["page_size"] == 10
            assert response_data["data"]["total_page"] == 1

    def test_get_user_list_default_parameters(self, client, mock_user):
        """测试获取用户列表默认参数"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.list_users.return_value = {
                "records": [mock_user],
                "total": 1,
                "page": 1,
                "page_size": 10,
                "total_page": 1
            }
            mock_service_class.return_value = mock_service
            
            # 不传递参数，使用默认值
            response = client.get("/users/list")
            
            assert response.status_code == 200
            mock_service.list_users.assert_called_once_with(1, 10)

    def test_get_user_list_invalid_parameters(self, client, mock_user):
        """测试获取用户列表无效参数"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.list_users.return_value = {
                "records": [mock_user],
                "total": 1,
                "page": 1,
                "page_size": 10,
                "total_page": 1
            }
            mock_service_class.return_value = mock_service
            
            # 测试无效参数会被修正
            test_cases = [
                {"page": -1, "expected_page": 1},  # 负数修正为1
                {"page": 0, "expected_page": 1},   # 0修正为1
                {"pageSize": -1, "expected_size": 10},  # 负数修正为10
                {"pageSize": 0, "expected_size": 10},   # 0修正为10
                {"pageSize": 101, "expected_size": 100}, # 超过限制修正为100
            ]
            
            for case in test_cases:
                mock_service.list_users.reset_mock()
                params = {}
                if "page" in case:
                    params["page"] = case["page"]
                if "pageSize" in case:
                    params["pageSize"] = case["pageSize"]
                
                response = client.get("/users/list", params=params)
                
                assert response.status_code == 200
                # 验证参数被修正
                call_args = mock_service.list_users.call_args[0]
                if "expected_page" in case:
                    assert call_args[0] == case["expected_page"]
                if "expected_size" in case:
                    assert call_args[1] == case["expected_size"]

    def test_get_user_detail_success(self, client, mock_user):
        """测试成功获取用户详情"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user.return_value = mock_user
            mock_service_class.return_value = mock_service
            
            response = client.get("/users/detail/1")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"] is not None

    def test_get_user_detail_not_found(self, client):
        """测试获取不存在用户详情"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            from app.core.exceptions import AppError
            
            mock_service = AsyncMock()
            mock_service.get_user.side_effect = AppError("用户 ID 999 不存在")
            mock_service_class.return_value = mock_service
            
            response = client.get("/users/detail/999")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is False
            assert "用户 ID 999 不存在" in response_data["message"]

    def test_get_user_detail_invalid_id(self, client):
        """测试获取用户详情时ID无效"""
        response = client.get("/users/detail/invalid")
        
        # FastAPI会自动验证路径参数，无效ID会返回422
        assert response.status_code == 422

    def test_update_user_success(self, client, mock_user):
        """测试成功更新用户"""
        update_data = {
            "email": "new@example.com",
            "full_name": "New Name"
        }
        
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user.return_value = mock_user
            mock_service_class.return_value = mock_service
            
            response = client.put("/users/update/1", json=update_data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"] is not None

    def test_update_user_not_found(self, client):
        """测试更新不存在的用户"""
        update_data = {"full_name": "New Name"}
        
        with patch('app.services.user_service.UserService') as mock_service_class:
            from app.core.exceptions import AppError
            
            mock_service = AsyncMock()
            mock_service.update_user.side_effect = AppError("用户 ID 999 不存在")
            mock_service_class.return_value = mock_service
            
            response = client.put("/users/update/999", json=update_data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is False
            assert "用户 ID 999 不存在" in response_data["message"]

    def test_update_user_invalid_data(self, client):
        """测试更新用户时数据无效"""
        # 无效邮箱格式
        invalid_data = {
            "email": "invalid-email-format"
        }
        
        response = client.put("/users/update/1", json=invalid_data)
        
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["success"] is False

    def test_update_user_empty_data(self, client, mock_user):
        """测试更新用户时数据为空"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.update_user.return_value = mock_user
            mock_service_class.return_value = mock_service
            
            # 空JSON对象
            response = client.put("/users/update/1", json={})
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True

    def test_delete_user_success(self, client):
        """测试成功删除用户"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.delete_user.return_value = True
            mock_service_class.return_value = mock_service
            
            response = client.delete("/users/delete/1")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["message"] == "用户删除成功"

    def test_delete_user_not_found(self, client):
        """测试删除不存在的用户"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            from app.core.exceptions import AppError
            
            mock_service = AsyncMock()
            mock_service.delete_user.side_effect = AppError("用户 ID 999 不存在")
            mock_service_class.return_value = mock_service
            
            response = client.delete("/users/delete/999")
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is False
            assert "用户 ID 999 不存在" in response_data["message"]

    def test_delete_user_invalid_id(self, client):
        """测试删除用户时ID无效"""
        response = client.delete("/users/delete/invalid")
        
        # FastAPI会自动验证路径参数，无效ID会返回422
        assert response.status_code == 422

    def test_api_error_handling(self, client):
        """测试API错误处理"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service
            
            response = client.get("/users/detail/1")
            
            # 应该返回500错误
            assert response.status_code == 500
            response_data = response.json()
            assert response_data["success"] is False

    def test_api_response_format_consistency(self, client, mock_user):
        """测试API响应格式一致性"""
        test_endpoints = [
            ("POST", "/users/add", {"user_name": "test", "password": "TestPass123!", "email": "test@example.com"}),
            ("GET", "/users/detail/1", None),
            ("PUT", "/users/update/1", {"full_name": "Test"}),
            ("DELETE", "/users/delete/1", None),
        ]
        
        for method, endpoint, data in test_endpoints:
            with patch('app.services.user_service.UserService') as mock_service_class:
                mock_service = AsyncMock()
                
                # 设置mock返回值
                if method == "POST":
                    mock_service.create_user.return_value = mock_user
                elif method == "GET":
                    mock_service.get_user.return_value = mock_user
                elif method == "PUT":
                    mock_service.update_user.return_value = mock_user
                elif method == "DELETE":
                    mock_service.delete_user.return_value = True
                
                mock_service_class.return_value = mock_service
                
                if method == "POST" or method == "PUT":
                    response = client.request(method, endpoint, json=data)
                else:
                    response = client.request(method, endpoint)
                
                # 验证响应格式一致性
                response_data = response.json()
                assert "success" in response_data
                assert "message" in response_data
                assert "data" in response_data

    def test_create_user_endpoint_structure(self, client):
        """测试创建用户端点结构"""
        # 这里主要测试端点结构，具体业务逻辑在集成测试中验证
        response = client.get("/docs")
        assert response.status_code == 200
        # 可以进一步验证用户端点的存在性

    def test_cors_headers(self, client):
        """测试CORS头"""
        response = client.options("/users/list")
        # 检查是否有CORS头（如果配置了CORS）
        # 这取决于实际的CORS配置

    def test_rate_limiting(self, client):
        """测试速率限制（如果配置了）"""
        # 快速发送多个请求
        for _ in range(10):
            response = client.get("/users/list")
            # 检查是否触发了速率限制
            # 这取决于实际的速率限制配置

    def test_authentication_required(self, client):
        """测试需要认证的端点（如果配置了认证）"""
        # 这取决于实际的认证配置
        # 如果端点需要认证，未认证请求应该返回401
        pass

    def test_authorization_required(self, client):
        """测试需要授权的端点（如果配置了授权）"""
        # 这取决于实际的授权配置
        # 如果端点需要特定权限，无权限请求应该返回403
        pass


class TestUserEndpointIntegration:
    """用户端点集成测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_full_user_workflow(self, client):
        """测试完整用户工作流"""
        # 这里可以测试创建 -> 查询 -> 更新 -> 删除的完整流程
        # 但需要真实的数据库连接，更适合在集成测试中进行
        pass

    def test_concurrent_requests(self, client):
        """测试并发请求"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/users/list")
            results.append(response.status_code)
        
        # 创建多个线程同时发请求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有请求都成功
        assert all(status == 200 for status in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
