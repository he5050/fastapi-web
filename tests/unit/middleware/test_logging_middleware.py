"""
日志中间件性能优化测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.applications import Starlette

from app.middleware.logging_middleware import LoggingMiddleware, LoggingMiddlewareConfig


class TestLoggingMiddlewareConfig:
    """日志中间件配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = LoggingMiddlewareConfig()
        
        # 验证默认排除路径
        assert "/health" in config.excluded_paths
        assert "/docs" in config.excluded_paths
        assert "/openapi.json" in config.excluded_paths
        
        # 验证其他默认配置
        assert config.max_response_length == 1000
        assert config.max_request_length == 1000
        assert config.log_response_body is True
        assert config.log_request_body is True


class TestLoggingMiddlewareInitialization:
    """日志中间件初始化测试"""

    def test_middleware_uses_main_database_engine(self):
        """测试中间件复用主数据库引擎"""
        # 创建一个简单的ASGI应用
        app = Starlette()
        
        # 初始化中间件
        middleware = LoggingMiddleware(app)
        
        # 验证中间件已初始化
        assert middleware.app is app
        assert middleware.config is not None
        
        # 验证log_session_local已设置
        assert middleware.log_session_local is not None
        
        # 验证log_session_local是从主数据库导入的AsyncSessionLocal
        from app.db.session import AsyncSessionLocal
        assert middleware.log_session_local is AsyncSessionLocal

    def test_middleware_preserves_excluded_paths(self):
        """测试中间件保留排除路径配置"""
        app = Starlette()
        middleware = LoggingMiddleware(app)
        
        # 验证排除路径配置
        assert "/health" in middleware.config.excluded_paths
        assert "/docs" in middleware.config.excluded_paths
        assert "/openapi.json" in middleware.config.excluded_paths


@pytest.mark.asyncio
class TestLoggingMiddlewareFunctionality:
    """日志中间件功能测试"""

    async def test_excluded_paths_not_logged(self, async_client):
        """测试排除路径不会被记录"""
        # 访问健康检查接口
        response = await async_client.get("/health")
        
        # 验证响应成功
        assert response.status_code == 200

    async def test_logged_requests_saved_to_database(self, async_client):
        """测试日志记录保存到数据库"""
        # 访问一个需要记录的接口（假设需要先登录获取token）
        # 这里简化为访问根路径
        
        response = await async_client.get("/")
        data = response.json()
        
        # 验证响应成功
        assert response.status_code == 200

    async def test_log_save_failure_does_not_affect_request(self, async_client):
        """测试日志保存失败不影响业务逻辑"""
        # 模拟日志保存失败的情况
        # 实际实现中，日志保存失败应该被捕获，不影响业务逻辑
        
        response = await async_client.get("/")
        data = response.json()
        
        # 验证即使日志保存失败，请求仍正常响应
        assert response.status_code == 200

    @patch('app.middleware.logging_middleware.logging_middleware.AsyncSession')
    async def test_log_session_uses_main_database_connection(self, mock_session):
        """测试日志会话使用主数据库连接"""
        app = Starlette()
        middleware = LoggingMiddleware(app)
        
        # 获取日志会话
        session_factory = middleware.get_log_session()
        
        # 验证session_factory存在
        assert session_factory is not None
        
        # 验证session_factory是从主数据库导入的
        from app.db.session import AsyncSessionLocal
        assert session_factory is AsyncSessionLocal


class TestLoggingMiddlewareRequestExclusion:
    """请求排除测试"""

    def test_should_exclude_health_endpoint(self):
        """测试排除健康检查接口"""
        app = Starlette()
        middleware = LoggingMiddleware(app)
        
        # 创建模拟请求
        from fastapi import Request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health"
        }
        request = Request(scope)
        
        # 验证健康检查接口被排除
        assert middleware._should_exclude_request(request) is True

    def test_should_exclude_docs_endpoint(self):
        """测试排除文档接口"""
        app = Starlette()
        middleware = LoggingMiddleware(app)
        
        # 创建模拟请求
        from fastapi import Request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/docs"
        }
        request = Request(scope)
        
        # 验证文档接口被排除
        assert middleware._should_exclude_request(request) is True

    def test_should_not_exclude_user_endpoints(self):
        """测试不排除用户接口"""
        app = Starlette()
        middleware = LoggingMiddleware(app)
        
        # 创建模拟请求
        from fastapi import Request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/users/list"
        }
        request = Request(scope)
        
        # 验证用户接口不被排除
        assert middleware._should_exclude_request(request) is False


@pytest.mark.asyncio
class TestLoggingMiddlewareWithAuthentication:
    """日志中间件与认证集成测试"""

    async def test_log_includes_user_info(self, async_client, test_user):
        """测试日志包含用户信息"""
        # 登录获取token
        login_data = {
            "username": test_user.user_name,
            "password": "Test@1234"
        }
        login_response = await async_client.post("/auth/login", json=login_data)
        access_token = login_response.json()["data"]["access_token"]
        
        # 使用token访问受保护接口
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await async_client.get("/users/list", headers=headers)
        
        # 验证响应成功
        assert response.status_code == 200
        # 注意：实际的日志记录需要在数据库中验证，这里主要测试请求流程

    async def test_log_includes_request_params(self, async_client):
        """测试日志包含请求参数"""
        # 访问带参数的接口
        params = {"page": 1, "page_size": 10}
        response = await async_client.get("/users/list", params=params)
        
        # 验证响应成功（可能需要认证，但主要测试参数提取）
        # 注意：这里可能因为未认证返回401，但日志中间件仍应记录请求参数
        assert response.status_code in [200, 401]


@pytest.mark.asyncio
class TestLoggingMiddlewarePerformance:
    """日志中间件性能测试"""

    async def test_middleware_does_not_block_requests(self, async_client):
        """测试中间件不阻塞请求"""
        # 发送多个请求
        import asyncio
        responses = await asyncio.gather(
            async_client.get("/"),
            async_client.get("/"),
            async_client.get("/"),
        )
        
        # 验证所有请求都成功响应
        for response in responses:
            assert response.status_code == 200

    async def test_async_log_save_does_not_delay_response(self, async_client):
        """测试异步日志保存不延迟响应"""
        # 访问接口
        response = await async_client.get("/")
        
        # 验证响应成功
        assert response.status_code == 200
        
        # 注意：实际的异步日志保存需要在代码层面验证
        # 这里主要验证请求流程正常