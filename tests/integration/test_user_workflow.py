import pytest
import asyncio
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate


class TestUserWorkflow:
    """用户工作流集成测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_user_creation_workflow(self):
        """测试用户创建完整工作流"""
        # 模拟数据库会话
        mock_db = AsyncMock(spec=AsyncSession)

        # 模拟repository方法
        mock_db_execute = AsyncMock()
        mock_db_scalar = AsyncMock(return_value=None)  # 模拟用户不存在
        mock_db.add = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # 创建用户服务实例
        service = UserService(mock_db)

        # 测试用户创建
        user_data = UserCreate(
            user_name="integrationuser",
            password="IntegrationPass123!",
            email="integration@example.com",
        )

        # 模拟repository方法
        service.repo.get_by_user_name = AsyncMock(return_value=None)
        service.repo.get_by_email = AsyncMock(return_value=None)
        service.repo.create = AsyncMock()

        # 执行用户创建
        try:
            await service.create_user(user_data)
            # 如果没有抛出异常，测试通过
            assert True
        except Exception as e:
            pytest.fail(f"User creation workflow failed: {e}")

    def test_api_endpoint_structure(self, client):
        """测试API端点结构完整性"""
        # 测试主要端点是否存在
        endpoints_to_check = ["/", "/docs", "/redoc"]

        for endpoint in endpoints_to_check:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} not accessible"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
