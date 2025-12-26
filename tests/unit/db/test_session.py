import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal, Base, get_db, check_db_connection


class TestDatabaseEngine:
    """数据库引擎测试"""

    def test_engine_exists(self):
        """测试数据库引擎存在"""
        from app.db.session import engine
        
        assert engine is not None
        assert isinstance(engine, AsyncEngine)

    def test_engine_configuration(self):
        """测试数据库引擎配置"""
        # 测试引擎基本属性
        assert hasattr(engine, 'url')
        assert hasattr(engine, 'pool')

    @patch('app.core.config.settings')
    def test_engine_with_different_settings(self, mock_settings):
        """测试不同配置下的数据库引擎"""
        mock_settings.async_database_url = "sqlite+aiosqlite:///test.db"
        mock_settings.DEBUG = False
        
        # 重新导入模块以测试不同配置
        import importlib
        import app.db.session
        importlib.reload(app.db.session)
        
        test_engine = app.db.session.engine
        assert test_engine is not None


class TestAsyncSessionLocal:
    """异步会话工厂测试"""

    def test_async_session_local_exists(self):
        """测试异步会话工厂存在"""
        assert AsyncSessionLocal is not None
        # 检查是否是sessionmaker实例
        assert hasattr(AsyncSessionLocal, '__call__')

    def test_async_session_local_configuration(self):
        """测试异步会话工厂配置"""
        # 测试会话工厂的基本属性
        assert hasattr(AsyncSessionLocal, 'class_')
        assert AsyncSessionLocal.class_ == AsyncSession
        assert AsyncSessionLocal.expire_on_commit is False


class TestBaseModel:
    """基础模型测试"""

    def test_base_model_exists(self):
        """测试基础模型存在"""
        assert Base is not None
        assert hasattr(Base, '__abstract__')

    def test_base_model_is_declarative_base(self):
        """测试基础模型是SQLAlchemy声明式基类"""
        from sqlalchemy.orm import DeclarativeBase
        
        # 检查Base是否是声明式基类
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, 'registry')

    def test_base_model_abstract_attribute(self):
        """测试基础模型的抽象属性"""
        assert Base.__abstract__ is True

    def test_base_model_inheritance(self):
        """测试基础模型继承"""
        from app.models.user_model import User
        
        # 验证User模型继承自Base
        assert issubclass(User, Base)


class TestGetDb:
    """获取数据库会话测试"""

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """测试获取数据库会话并生成"""
        with patch('app.db.session.AsyncSessionLocal') as mock_session_local:
            # 模拟会话上下文管理器
            mock_session = AsyncMock(spec=AsyncSession)
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_context_manager
            
            # 测试生成器
            db_gen = get_db()
            
            # 获取会话
            session = await db_gen.__anext__()
            
            assert session == mock_session
            
            # 关闭生成器
            try:
                await db_gen.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_get_db_session_closing(self):
        """测试数据库会话关闭"""
        with patch('app.db.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_context_manager
            
            db_gen = get_db()
            session = await db_gen.__anext__()
            
            # 确保会话被关闭
            mock_session.close.assert_not_called()  # close在finally块中调用
            
            # 清理生成器
            try:
                await db_gen.__anext__()
            except StopAsyncIteration:
                pass
            
            # 验证会话关闭被调用
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_with_exception(self):
        """测试获取数据库会话时发生异常"""
        with patch('app.db.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.close = AsyncMock()
            
            # 模拟会话创建时的异常
            mock_session_local.side_effect = Exception("Database connection failed")
            
            db_gen = get_db()
            
            # 应该抛出异常
            with pytest.raises(Exception, match="Database connection failed"):
                await db_gen.__anext__()

    @pytest.mark.asyncio
    async def test_get_db_context_manager_behavior(self):
        """测试获取数据库会话的上下文管理器行为"""
        with patch('app.db.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.close = AsyncMock()
            
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_context_manager
            
            # 使用async with语句
            async with get_db() as session:
                assert session == mock_session
                # 验证会话没有被关闭
                mock_session.close.assert_not_called()
            
            # 验证会话被关闭
            mock_session.close.assert_called_once()


class TestCheckDbConnection:
    """检查数据库连接测试"""

    @pytest.mark.asyncio
    @patch('app.db.session.engine')
    @patch('builtins.print')
    async def test_check_db_connection_success(self, mock_print, mock_engine):
        """测试数据库连接成功"""
        # 模拟成功的连接
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = AsyncMock()
        
        result = await check_db_connection()
        
        assert result is True
        
        # 验证输出消息
        mock_print.assert_any_call("✅ 数据库连接成功!")
        mock_engine.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.db.session.engine')
    @patch('app.db.session.settings')
    @patch('builtins.print')
    async def test_check_db_connection_failure(self, mock_print, mock_settings, mock_engine):
        """测试数据库连接失败"""
        # 模拟连接失败
        mock_engine.connect.side_effect = Exception("Connection failed")
        mock_settings.async_database_url = "mysql+aiomysql://user:pass@host:3306/db"
        
        result = await check_db_connection()
        
        assert result is False
        
        # 验证错误消息
        mock_print.assert_any_call("❌ 数据库连接失败: Connection failed")
        mock_print.assert_any_call("🔍 尝试连接的地址: mysql+aiomysql://user:pass@host:3306/db")

    @pytest.mark.asyncio
    @patch('app.db.session.engine')
    @patch('builtins.print')
    async def test_check_db_connection_with_text_query(self, mock_print, mock_engine):
        """测试数据库连接查询文本"""
        mock_conn = AsyncMock()
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = AsyncMock()
        
        await check_db_connection()
        
        # 验证执行了正确的查询
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0][0]
        assert str(call_args) == "SELECT 1"

    @pytest.mark.asyncio
    @patch('app.db.session.engine')
    @patch('builtins.print')
    async def test_check_db_connection_exception_handling(self, mock_print, mock_engine):
        """测试数据库连接异常处理"""
        # 测试不同类型的异常
        exceptions = [
            ConnectionError("Connection refused"),
            TimeoutError("Connection timeout"),
            ValueError("Invalid database URL"),
            RuntimeError("Database error"),
        ]
        
        for exc in exceptions:
            mock_print.reset_mock()
            mock_engine.connect.side_effect = exc
            
            result = await check_db_connection()
            
            assert result is False
            mock_print.assert_any_call(f"❌ 数据库连接失败: {str(exc)}")

    @pytest.mark.asyncio
    @patch('app.db.session.engine')
    @patch('app.db.session.settings')
    @patch('builtins.print')
    async def test_check_db_connection_with_none_settings(self, mock_print, mock_settings, mock_engine):
        """测试数据库连接时配置为None"""
        mock_engine.connect.side_effect = Exception("No connection")
        mock_settings.async_database_url = None
        
        result = await check_db_connection()
        
        assert result is False
        mock_print.assert_any_call("🔍 尝试连接的地址: None")

    @pytest.mark.asyncio
    @patch('app.db.session.engine')
    @patch('builtins.print')
    async def test_check_db_connection_sqlalchemy_error(self, mock_print, mock_engine):
        """测试SQLAlchemy特定错误"""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_engine.connect.side_effect = SQLAlchemyError("SQLAlchemy error")
        
        result = await check_db_connection()
        
        assert result is False
        mock_print.assert_any_call("❌ 数据库连接失败: SQLAlchemy error")


class TestDatabaseSessionIntegration:
    """数据库会话集成测试"""

    def test_session_and_engine_relationship(self):
        """测试会话和引擎的关系"""
        # 验证会话工厂使用正确的引擎
        assert AsyncSessionLocal.bind == engine

    def test_base_model_registry(self):
        """测试基础模型注册表"""
        # 验证Base有正确的注册表
        assert hasattr(Base, 'registry')
        assert hasattr(Base, 'metadata')

    def test_database_configuration_consistency(self):
        """测试数据库配置一致性"""
        from app.core.config import settings
        
        # 验证引擎URL与配置一致
        assert str(engine.url) == settings.async_database_url

    @pytest.mark.asyncio
    async def test_multiple_sessions_independence(self):
        """测试多个会话的独立性"""
        with patch('app.db.session.AsyncSessionLocal') as mock_session_local:
            sessions = []
            
            for i in range(3):
                mock_session = AsyncMock(spec=AsyncSession)
                mock_context_manager = AsyncMock()
                mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
                mock_context_manager.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_context_manager
                
                db_gen = get_db()
                session = await db_gen.__anext__()
                sessions.append(session)
            
            # 验证每个会话都是独立的
            assert len(set(sessions)) == 3

    def test_session_configuration_parameters(self):
        """测试会话配置参数"""
        # 验证会话工厂的配置
        assert AsyncSessionLocal.expire_on_commit is False
        assert AsyncSessionLocal.class_ == AsyncSession
