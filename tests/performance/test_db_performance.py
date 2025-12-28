false</ask>
<![CDATA[
"""
数据库性能测试
"""
import asyncio
import pytest
from sqlalchemy import text
from app.db.session import engine, get_db
from app.core.config import settings


async def test_connection_pool_config():
    """测试连接池配置是否生效"""
    # 检查引擎配置
    assert engine.pool.size() == settings.DB_POOL_SIZE
    assert engine.pool.max_overflow == settings.DB_MAX_OVERFLOW
    assert engine.pool.timeout == settings.DB_POOL_TIMEOUT
    assert engine.pool.recycle == settings.DB_POOL_RECYCLE
    print("✅ 连接池配置验证通过")


async def test_multiple_concurrent_connections():
    """测试并发连接"""
    connection_count = 10
    
    async def make_connection():
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar()
    
    # 并发创建多个连接
    tasks = [make_connection() for _ in range(connection_count)]
    results = await asyncio.gather(*tasks)
    
    # 验证所有连接都成功
    assert all(results == [1] * connection_count)
    print(f"✅ 成功处理 {connection_count} 个并发连接")


async def test_connection_timeout():
    """测试连接超时"""
    # 这个测试需要根据实际情况调整
    # 在实际环境中，可能需要模拟连接耗尽的情况
    pass


@pytest.mark.asyncio
async def test_database_indexes():
    """测试数据库索引是否存在"""
    async with engine.connect() as conn:
        # 检查用户表索引
        result = await conn.execute(text("""
            SHOW INDEX FROM sys_users 
            WHERE Key_name IN ('idx_user_name_email', 'idx_created_at')
        """))
        indexes = result.fetchall()
        
        # 验证复合索引存在
        index_names = [index[2] for index in indexes]
        assert 'idx_user_name_email' in index_names
        assert 'idx_created_at' in index_names
        
        print("✅ 数据库索引验证通过")
证通过")
