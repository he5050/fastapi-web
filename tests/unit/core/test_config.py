import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from app.core.config import Settings, get_settings, settings, print_config_info


class TestSettings:
    """配置类测试"""

    def test_settings_default_values(self):
        """测试配置默认值"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('app.core.config.BASE_DIR', Path('/tmp')):
                test_settings = Settings()
                
                assert test_settings.APP_NAME == "FastAPI Web"
                assert test_settings.APP_ENV == "dev"
                assert test_settings.APP_PORT == 8000
                assert test_settings.DEBUG is True
                assert test_settings.DB_HOST == "127.0.0.1"
                assert test_settings.DB_PORT == 3306
                assert test_settings.DB_USER == "root"
                assert test_settings.DB_PASSWORD == ""
                assert test_settings.DB_NAME == "test"
                assert test_settings.DB_CHARSET == "utf8mb4"
                assert test_settings.LOG_LEVEL == "INFO"

    def test_settings_from_env_variables(self):
        """测试从环境变量加载配置"""
        env_vars = {
            'APP_NAME': 'Test App',
            'APP_ENV': 'prod',
            'APP_PORT': '9000',
            'DEBUG': 'false',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'LOG_LEVEL': 'DEBUG',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('app.core.config.BASE_DIR', Path('/tmp')):
                test_settings = Settings()
                
                assert test_settings.APP_NAME == 'Test App'
                assert test_settings.APP_ENV == 'prod'
                assert test_settings.APP_PORT == 9000
                assert test_settings.DEBUG is False
                assert test_settings.DB_HOST == 'localhost'
                assert test_settings.DB_PORT == 5432
                assert test_settings.DB_USER == 'testuser'
                assert test_settings.DB_PASSWORD == 'testpass'
                assert test_settings.DB_NAME == 'testdb'
                assert test_settings.LOG_LEVEL == 'DEBUG'

    def test_async_database_url_property(self):
        """测试异步数据库URL构造"""
        test_settings = Settings(
            DB_USER="testuser",
            DB_PASSWORD="testpass",
            DB_HOST="localhost",
            DB_PORT=5432,
            DB_NAME="testdb",
            DB_CHARSET="utf8mb4"
        )
        
        expected_url = "mysql+aiomysql://testuser:testpass@localhost:5432/testdb?charset=utf8mb4"
        assert test_settings.async_database_url == expected_url

    def test_async_database_url_with_empty_password(self):
        """测试空密码的数据库URL构造"""
        test_settings = Settings(
            DB_USER="testuser",
            DB_PASSWORD="",
            DB_HOST="localhost",
            DB_PORT=3306,
            DB_NAME="testdb",
            DB_CHARSET="utf8mb4"
        )
        
        expected_url = "mysql+aiomysql://testuser:@localhost:3306/testdb?charset=utf8mb4"
        assert test_settings.async_database_url == expected_url

    @patch('app.core.config.os.path.join')
    @patch('app.core.config.os.getenv')
    def test_settings_model_config_env_file(self, mock_getenv, mock_join):
        """测试配置模型的环境文件配置"""
        mock_getenv.return_value = 'test'
        mock_join.return_value = '/tmp/.env.test'
        
        # 重新导入配置以触发环境变量设置
        from importlib import reload
        import app.core.config
        reload(app.core.config)
        
        # 验证环境文件路径设置
        mock_join.assert_called_with(Path('/tmp'), '.env.test')

    def test_settings_extra_ignore(self):
        """测试额外配置字段被忽略"""
        env_vars = {
            'UNKNOWN_FIELD': 'should_be_ignored',
            'APP_NAME': 'Test App',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('app.core.config.BASE_DIR', Path('/tmp')):
                test_settings = Settings()
                
                assert test_settings.APP_NAME == 'Test App'
                assert not hasattr(test_settings, 'UNKNOWN_FIELD')


class TestGetSettings:
    """获取配置函数测试"""

    @patch('app.core.config.os.getenv')
    @patch('app.core.config.Settings')
    def test_get_settings_caches_result(self, mock_settings_class, mock_getenv):
        """测试配置单例缓存"""
        mock_getenv.return_value = 'test'
        mock_settings_instance = MagicMock()
        mock_settings_class.return_value = mock_settings_instance
        
        # 第一次调用
        result1 = get_settings()
        
        # 第二次调用
        result2 = get_settings()
        
        # 应该返回同一个实例
        assert result1 is result2
        mock_settings_class.assert_called_once()

    @patch('app.core.config.os.getenv')
    @patch('app.core.config.os.environ')
    @patch('app.core.config.Settings')
    def test_get_settings_sets_default_env(self, mock_settings_class, mock_environ, mock_getenv):
        """测试设置默认环境变量"""
        mock_getenv.return_value = None  # 环境变量未设置
        mock_settings_instance = MagicMock()
        mock_settings_class.return_value = mock_settings_instance
        
        get_settings()
        
        # 验证设置了默认环境变量
        mock_environ.__setitem__.assert_called_once_with("APP_ENV", "dev")

    @patch('app.core.config.os.getenv')
    def test_get_settings_with_existing_env(self, mock_getenv):
        """测试已存在环境变量的情况"""
        mock_getenv.return_value = 'production'
        
        with patch('app.core.config.Settings') as mock_settings_class:
            mock_settings_instance = MagicMock()
            mock_settings_class.return_value = mock_settings_instance
            
            get_settings()
            
            # 不应该修改环境变量
            mock_getenv.assert_called_with("APP_ENV")


class TestSettingsInstance:
    """配置实例测试"""

    def test_settings_instance_exists(self):
        """测试配置实例存在"""
        from app.core.config import settings
        
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_instance_properties(self):
        """测试配置实例属性"""
        from app.core.config import settings
        
        # 测试基本属性存在
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'APP_ENV')
        assert hasattr(settings, 'async_database_url')


class TestPrintConfigInfo:
    """打印配置信息测试"""

    @patch('builtins.print')
    def test_print_config_info_outputs_expected_format(self, mock_print):
        """测试配置信息输出格式"""
        test_settings = Settings(
            APP_ENV='test',
            DEBUG=True,
            DB_HOST='localhost',
            DB_PORT=3306,
            DB_NAME='testdb',
            LOG_LEVEL='INFO',
            APP_PORT=8000
        )
        
        with patch('app.core.config.settings', test_settings):
            print_config_info()
        
        # 验证print被调用了正确的次数
        assert mock_print.call_count == 7  # 6行输出 + 1个分隔线
        
        # 验证输出内容
        call_args = [call.args[0] for call in mock_print.call_args_list]
        
        # 检查关键信息
        assert any("应用启动中" in str(arg) for arg in call_args)
        assert any("当前环境: test" in str(arg) for arg in call_args)
        assert any("调试模式: 开启" in str(arg) for arg in call_args)
        assert any("数据库: localhost:3306/testdb" in str(arg) for arg in call_args)
        assert any("日志级别: INFO" in str(arg) for arg in call_args)
        assert any("API文档: http://127.0.0.1:8000/docs" in str(arg) for arg in call_args)

    @patch('builtins.print')
    def test_print_config_info_with_debug_false(self, mock_print):
        """测试调试模式关闭时的输出"""
        test_settings = Settings(
            APP_ENV='production',
            DEBUG=False,
            DB_HOST='localhost',
            DB_PORT=3306,
            DB_NAME='testdb',
            LOG_LEVEL='ERROR',
            APP_PORT=9000
        )
        
        with patch('app.core.config.settings', test_settings):
            print_config_info()
        
        call_args = [call.args[0] for call in mock_print.call_args_list]
        
        assert any("调试模式: 关闭" in str(arg) for arg in call_args)
        assert any("当前环境: production" in str(arg) for arg in call_args)
        assert any("日志级别: ERROR" in str(arg) for arg in call_args)
        assert any("API文档: http://127.0.0.1:9000/docs" in str(arg) for arg in call_args)


class TestConfigEdgeCases:
    """配置边界情况测试"""

    def test_database_url_with_special_characters(self):
        """测试包含特殊字符的数据库URL"""
        test_settings = Settings(
            DB_USER="user@domain",
            DB_PASSWORD="p@ssw0rd!",
            DB_HOST="host-name",
            DB_PORT=3306,
            DB_NAME="db_name",
            DB_CHARSET="utf8mb4"
        )
        
        url = test_settings.async_database_url
        assert "user@domain" in url
        assert "p@ssw0rd!" in url
        assert "host-name" in url
        assert "db_name" in url

    def test_port_conversion(self):
        """测试端口转换"""
        env_vars = {
            'APP_PORT': '9000',
            'DB_PORT': '5432',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('app.core.config.BASE_DIR', Path('/tmp')):
                test_settings = Settings()
                
                assert test_settings.APP_PORT == 9000
                assert test_settings.DB_PORT == 5432
                assert isinstance(test_settings.APP_PORT, int)
                assert isinstance(test_settings.DB_PORT, int)

    def test_boolean_conversion(self):
        """测试布尔值转换"""
        test_cases = [
            {'DEBUG': 'true', 'expected': True},
            {'DEBUG': 'True', 'expected': True},
            {'DEBUG': 'TRUE', 'expected': True},
            {'DEBUG': 'false', 'expected': False},
            {'DEBUG': 'False', 'expected': False},
            {'DEBUG': 'FALSE', 'expected': False},
        ]
        
        for case in test_cases:
            with patch.dict(os.environ, case, clear=True):
                with patch('app.core.config.BASE_DIR', Path('/tmp')):
                    test_settings = Settings()
                    assert test_settings.DEBUG == case['expected']

    def test_invalid_port_values(self):
        """测试无效端口值的处理"""
        env_vars = {
            'APP_PORT': 'invalid',
            'DB_PORT': 'not_a_number',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('app.core.config.BASE_DIR', Path('/tmp')):
                # 应该使用默认值
                test_settings = Settings()
                assert test_settings.APP_PORT == 8000
                assert test_settings.DB_PORT == 3306
