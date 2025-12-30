# 基础配置
APP_NAME=FastAPI Web API (Production)
APP_ENV=pro
APP_PORT=8080
DEBUG=false

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME="fastapi_web"
DB_CHARSET="utf8mb4"
DB_INIT=false

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=2
REDIS_TIMEOUT=10

# JWT配置（生产环境请务必修改SECRET_KEY）
SECRET_KEY=production-secret-key-must-be-changed-very-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# 日志配置
LOG_LEVEL=INFO
