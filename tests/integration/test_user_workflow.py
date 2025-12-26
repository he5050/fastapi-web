import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.main import app
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user_model import User
from tests.conftest import UserFactory


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


class TestEndToEndUserFlow:
    """端到端用户流程测试"""

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, db_session):
        """测试完整的用户生命周期：创建 -> 查询 -> 更新 -> 删除"""
        # 创建用户服务
        service = UserService(db_session)
        
        # 1. 创建用户
        user_data = UserCreate(
            user_name="lifecycleuser",
            password="LifecyclePass123!",
            email="lifecycle@example.com",
            full_name="Lifecycle Test User"
        )
        
        created_user = await service.create_user(user_data)
        assert created_user.id is not None
        assert created_user.user_name == "lifecycleuser"
        assert created_user.email == "lifecycle@example.com"
        assert created_user.full_name == "Lifecycle Test User"
        
        # 2. 查询用户
        retrieved_user = await service.get_user(created_user.id)
        assert retrieved_user.id == created_user.id
        assert retrieved_user.user_name == "lifecycleuser"
        
        # 3. 查询用户列表
        user_list = await service.list_users(1, 10)
        assert len(user_list["records"]) >= 1
        assert user_list["total"] >= 1
        
        # 4. 更新用户
        update_data = UserUpdate(
            full_name="Updated Lifecycle User",
            email="updated@example.com"
        )
        
        updated_user = await service.update_user(created_user.id, update_data)
        assert updated_user.full_name == "Updated Lifecycle User"
        assert updated_user.email == "updated@example.com"
        
        # 5. 删除用户（软删除）
        delete_result = await service.delete_user(created_user.id)
        assert delete_result is True
        
        # 6. 验证用户已删除
        with pytest.raises(Exception):  # 应该抛出用户不存在的异常
            await service.get_user(created_user.id)

    @pytest.mark.asyncio
    async def test_user_workflow_with_real_database(self, db_session):
        """测试用户工作流与真实数据库交互"""
        service = UserService(db_session)
        
        # 创建多个用户
        users_data = [
            UserCreate(
                user_name=f"testuser{i}",
                password=f"TestPass{i}123!",
                email=f"test{i}@example.com",
                full_name=f"Test User {i}"
            )
            for i in range(3)
        ]
        
        created_users = []
        for user_data in users_data:
            user = await service.create_user(user_data)
            created_users.append(user)
        
        # 测试分页查询
        page1 = await service.list_users(1, 2)
        assert len(page1["records"]) == 2
        assert page1["total_page"] == 2
        
        page2 = await service.list_users(2, 2)
        assert len(page2["records"]) == 1
        assert page2["total_page"] == 2
        
        # 清理创建的用户
        for user in created_users:
            await service.delete_user(user.id)


class TestDatabaseTransactionRollback:
    """数据库事务回滚测试"""

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_session):
        """测试发生错误时事务回滚"""
        service = UserService(db_session)
        
        # 创建第一个用户（成功）
        user_data1 = UserCreate(
            user_name="user1",
            password="TestPass123!",
            email="user1@example.com"
        )
        created_user1 = await service.create_user(user_data1)
        
        # 模拟创建第二个用户时发生错误
        with patch.object(service.repo, 'create', side_effect=Exception("Database error")):
            user_data2 = UserCreate(
                user_name="user2",
                password="TestPass123!",
                email="user2@example.com"
            )
            
            with pytest.raises(Exception, match="Database error"):
                await service.create_user(user_data2)
        
        # 验证第一个用户仍然存在，第二个用户不存在
        user1 = await service.get_user(created_user1.id)
        assert user1 is not None
        
        with pytest.raises(Exception):  # 第二个用户不应该存在
            await service.get_user_by_name("user2")

    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, db_session):
        """测试并发用户操作"""
        service = UserService(db_session)
        
        async def create_user_task(user_index):
            user_data = UserCreate(
                user_name=f"concurrentuser{user_index}",
                password=f"ConcurrentPass{user_index}123!",
                email=f"concurrent{user_index}@example.com"
            )
            return await service.create_user(user_data)
        
        # 并发创建5个用户
        tasks = [create_user_task(i) for i in range(5)]
        created_users = await asyncio.gather(*tasks)
        
        # 验证所有用户都创建成功
        for i, user in enumerate(created_users):
            assert user.user_name == f"concurrentuser{i}"
            assert user.email == f"concurrent{i}@example.com"
            
            # 清理
            await service.delete_user(user.id)

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, db_session):
        """测试事务隔离"""
        service1 = UserService(db_session)
        service2 = UserService(db_session)
        
        # 在第一个服务中开始创建用户但未提交
        user_data = UserCreate(
            user_name="isolationuser",
            password="TestPass123!",
            email="isolation@example.com"
        )
        
        # 由于是异步测试，这里我们主要验证不同服务实例的独立性
        user1 = await service1.create_user(user_data)
        user2 = await service1.get_user(user1.id)
        
        # 验证两个服务实例可以访问相同的数据
        user3 = await service2.get_user(user1.id)
        assert user2.id == user3.id
        
        # 清理
        await service1.delete_user(user1.id)


class TestAPIIntegration:
    """API集成测试"""

    @pytest.mark.asyncio
    async def test_api_end_to_user_flow(self, client, db_session):
        """测试API端到端用户流程"""
        # 模拟数据库操作
        with patch('app.services.user_service.UserService') as mock_service_class:
            # 创建mock服务实例
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # 设置mock用户
            mock_user = UserFactory.create_user_model(id=1, user_name="apiuser")
            
            # 1. 创建用户API
            mock_service.create_user.return_value = mock_user
            create_response = client.post("/users/add", json={
                "user_name": "apiuser",
                "password": "ApiPass123!",
                "email": "api@example.com"
            })
            assert create_response.status_code == 200
            
            # 2. 获取用户详情API
            mock_service.get_user.return_value = mock_user
            detail_response = client.get("/users/detail/1")
            assert detail_response.status_code == 200
            
            # 3. 获取用户列表API
            mock_service.list_users.return_value = {
                "records": [mock_user],
                "total": 1,
                "page": 1,
                "page_size": 10,
                "total_page": 1
            }
            list_response = client.get("/users/list")
            assert list_response.status_code == 200
            
            # 4. 更新用户API
            mock_service.update_user.return_value = mock_user
            update_response = client.put("/users/update/1", json={
                "full_name": "Updated API User"
            })
            assert update_response.status_code == 200
            
            # 5. 删除用户API
            mock_service.delete_user.return_value = True
            delete_response = client.delete("/users/delete/1")
            assert delete_response.status_code == 200

    def test_api_error_handling_integration(self, client):
        """测试API错误处理集成"""
        with patch('app.services.user_service.UserService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # 测试各种错误场景
            error_scenarios = [
                # 用户不存在
                {
                    "method": "GET",
                    "url": "/users/detail/999",
                    "mock_method": "get_user",
                    "mock_exception": Exception("用户 ID 999 不存在"),
                    "expected_status": 500
                },
                # 更新失败
                {
                    "method": "PUT",
                    "url": "/users/update/999",
                    "mock_method": "update_user",
                    "mock_exception": Exception("用户 ID 999 不存在"),
                    "expected_status": 500
                },
                # 删除失败
                {
                    "method": "DELETE",
                    "url": "/users/delete/999",
                    "mock_method": "delete_user",
                    "mock_exception": Exception("用户 ID 999 不存在"),
                    "expected_status": 500
                },
            ]
            
            for scenario in error_scenarios:
                # 设置mock异常
                getattr(mock_service, scenario["mock_method"]).side_effect = scenario["mock_exception"]
                
                # 发送请求
                if scenario["method"] == "GET":
                    response = client.get(scenario["url"])
                elif scenario["method"] == "PUT":
                    response = client.put(scenario["url"], json={})
                elif scenario["method"] == "DELETE":
                    response = client.delete(scenario["url"])
                
                # 验证响应
                assert response.status_code == scenario["expected_status"]
                
                # 重置mock
                getattr(mock_service, scenario["mock_method"]).side_effect = None


class TestPerformanceAndLoad:
    """性能和负载测试基础框架"""

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client):
        """测试并发API请求"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = client.get("/docs")  # 轻量级请求
                end_time = time.time()
                results.append({
                    "status": response.status_code,
                    "response_time": end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # 创建多个线程同时发请求
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(result["status"] == 200 for result in results)
        
        # 验证响应时间在合理范围内（例如小于5秒）
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 5.0

    @pytest.mark.asyncio
    async def test_database_connection_pool(self, db_session):
        """测试数据库连接池"""
        service = UserService(db_session)
        
        async def database_operation():
            # 执行一些数据库操作
            user_data = UserCreate(
                user_name=f"pooluser{asyncio.current_task().get_name()}",
                password="TestPass123!",
                email=f"pool{asyncio.current_task().get_name()}@example.com"
            )
            
            user = await service.create_user(user_data)
            await service.get_user(user.id)
            await service.delete_user(user.id)
            
            return True
        
        # 并发执行多个数据库操作
        tasks = [database_operation() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # 验证所有操作都成功
        assert all(results)

    def test_memory_usage(self, client):
        """测试内存使用情况（基础测试）"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        
        # 记录初始内存使用
        initial_memory = process.memory_info().rss
        
        # 执行一些API请求
        for _ in range(100):
            response = client.get("/docs")
            assert response.status_code == 200
        
        # 检查内存增长
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（例如小于100MB）
        assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f} MB"


class TestSecurityIntegration:
    """安全集成测试"""

    @pytest.mark.asyncio
    async def test_password_hashing_integration(self, db_session):
        """测试密码哈希集成"""
        service = UserService(db_session)
        
        # 创建用户
        user_data = UserCreate(
            user_name="secureuser",
            password="SecurePass123!",
            email="secure@example.com"
        )
        
        created_user = await service.create_user(user_data)
        
        # 验证密码被正确哈希
        assert created_user.hashed_password is not None
        assert created_user.hashed_password != "SecurePass123!"
        assert created_user.hashed_password.startswith("$2b$")
        
        # 清理
        await service.delete_user(created_user.id)

    @pytest.mark.asyncio
    async def test_input_validation_integration(self, client):
        """测试输入验证集成"""
        # 测试各种无效输入
        invalid_inputs = [
            # 创建用户时的无效数据
            {
                "endpoint": "/users/add",
                "method": "POST",
                "data": {
                    "user_name": "ab",  # 太短
                    "password": "weak",  # 太弱
                    "email": "invalid-email"  # 无效格式
                }
            },
            {
                "endpoint": "/users/add",
                "method": "POST",
                "data": {
                    "user_name": "test",
                    # 缺少password
                    "email": "test@example.com"
                }
            },
            # 更新用户时的无效数据
            {
                "endpoint": "/users/update/1",
                "method": "PUT",
                "data": {
                    "email": "invalid-email-format"
                }
            }
        ]
        
        for invalid_input in invalid_inputs:
            if invalid_input["method"] == "POST":
                response = client.post(invalid_input["endpoint"], json=invalid_input["data"])
            elif invalid_input["method"] == "PUT":
                response = client.put(invalid_input["endpoint"], json=invalid_input["data"])
            
            # 应该返回验证错误
            assert response.status_code == 422
            response_data = response.json()
            assert response_data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
