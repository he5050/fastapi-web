#!/bin/bash

# 加载环境变量
set -a
[ -f .env.dev ] && . .env.dev
[ -f .env.local ] && . .env.local
set +a

# 设置默认值
APP_PORT=${APP_PORT:-8000}
APP_ENV=${APP_ENV:-dev}

echo "🚀 Using uv to start FastAPI in $APP_ENV mode on port $APP_PORT..."

# 使用 uv 启动 uvicorn
# --reload 仅在非生产环境下开启
if [ "$APP_ENV" == "pro" ]; then
    uv run uvicorn app.main:app --host 0.0.0.0 --port $APP_PORT
else
    uv run uvicorn app.main:app --host 127.0.0.1 --port $APP_PORT --reload
fi
