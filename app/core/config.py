import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    配置类，支持多环境
    """

    # 基础配置
    APP_NAME: str = "FastAPI Web"  # 应用名称
    APP_ENV: str = "local"  # 环境变量
    APP_PORT: int = 8000  # 应用端口
    DEBUG: bool = True  # 是否开启调试模式

    # 数据库配置
    DB_HOST: str = "127.0.0.1"  # 数据库地址
    DB_PORT: int = 3306  # 数据库端口
    DB_USER: str = "root"  # 数据库用户名
    DB_PASSWORD: str = ""  # 数据库密码
    DB_NAME: str = "test"  # 数据库名称
    DB_CHARSET: str = "utf8mb4"  # 数据库编码
    DB_INIT: bool = False  # 是否初始化数据库

    # 数据库连接池配置
    DB_POOL_SIZE: int = 20  # 连接池大小
    DB_MAX_OVERFLOW: int = 40  # 连接池最大溢出量
    DB_POOL_TIMEOUT: int = 30  # 连接池超时时间
    DB_POOL_RECYCLE: int = 3600  # 连接池重用时间

    # 日志配置
    LOG_LEVEL: str = "INFO"  # 日志级别

    # CORS配置
    CORS_ORIGINS: list[str] = ["*"]  # 生产环境应该具体配置
    CORS_ALLOW_CREDENTIALS: bool = True  # 是否允许凭据
    CORS_ALLOW_METHODS: list[str] = ["*"]  # 允许的方法
    CORS_ALLOW_HEADERS: list[str] = ["*"]  # 允许的头部

    # 自动识别环境并加载对应的 .env 文件
    # 优先使用 local 环境，如果不存在则使用 dev
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, f".env.{os.getenv('APP_ENV', 'local')}"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        """
        构造异步数据库连接字符串
        """
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"


@lru_cache()
def get_settings():
    """
    缓存配置单例
    """
    # 如果环境变量未设置，优先使用 local，如果不存在则使用 dev
    if not os.getenv("APP_ENV"):
        # 检查 local 环境文件是否存在
        local_env_file = BASE_DIR / ".env.local"
        if local_env_file.exists():
            os.environ["APP_ENV"] = "local"
        else:
            os.environ["APP_ENV"] = "dev"
    return Settings()


settings = get_settings()


def print_config_info():
    """
    打印基础配置信息 (启动时调用)
    """
    print("=" * 60)
    print("🚀 应用启动中...")
    print(f"🌍 当前环境: {settings.APP_ENV}")
    print(f"📦 应用名称: {settings.APP_NAME}")
    print(f"🔧 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print(f"🌐 服务端口: {settings.APP_PORT}")

    # 数据库配置信息
    print("🗄️ 数据库配置:")
    print(f"   📍 地址: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"   📂 名称: {settings.DB_NAME}")
    print(f"   👤 用户: {settings.DB_USER}")
    print(
        f"   🔑 密码: {'*' * len(settings.DB_PASSWORD) if settings.DB_PASSWORD else '未设置'}"
    )
    print(f"   📝 编码: {settings.DB_CHARSET}")

    # 连接池配置
    print("🔗 连接池配置:")
    print(f"   📊 池大小: {settings.DB_POOL_SIZE}")
    print(f"   📈 最大溢出: {settings.DB_MAX_OVERFLOW}")
    print(f"   ⏱️  超时: {settings.DB_POOL_TIMEOUT}s")
    print(f"   🔄 回收时间: {settings.DB_POOL_RECYCLE}s")

    # 数据库初始化状态
    print(f"📋 数据库初始化: {'启用' if settings.DB_INIT else '禁用'}")

    # 日志和其他配置
    print(f"📜 日志级别: {settings.LOG_LEVEL}")
    print(
        f"🌍 CORS允许源: {', '.join(settings.CORS_ORIGINS[:3])}{'...' if len(settings.CORS_ORIGINS) > 3 else ''}"
    )
    print(f"📄 API文档: http://127.0.0.1:{settings.APP_PORT}/docs")
    print("=" * 60)
