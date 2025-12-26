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
    APP_NAME: str = "FastAPI Web"
    APP_ENV: str = "local"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # 数据库配置
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "test"
    DB_CHARSET: str = "utf8mb4"
    DB_INIT: bool = False

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # CORS配置
    CORS_ORIGINS: list[str] = ["*"]  # 生产环境应该具体配置
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

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
    print("=" * 50)
    print("🚀 应用启动中...")
    print(f"🌍 当前环境: {settings.APP_ENV}")
    print(f"🛠️  调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print(f"📦 数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"📜 日志级别: {settings.LOG_LEVEL}")
    print(f"📄 API文档: http://127.0.0.1:{settings.APP_PORT}/docs")
    print("=" * 50)
