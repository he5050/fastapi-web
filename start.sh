#!/bin/bash

# 获取命令行参数，默认为 local（优先使用 local，不存在则用 dev）
ENV_ARG=${1:-local}

# 如果指定的是 local 但文件不存在，则回退到 dev
if [ "$ENV_ARG" == "local" ] && [ ! -f ".env.local" ]; then
    ENV_ARG="dev"
fi

# 加载环境变量
set -a
if [ -f ".env.$ENV_ARG" ]; then
    . ".env.$ENV_ARG"
    echo "📋 已加载环境配置文件: .env.$ENV_ARG"
else
    echo "⚠️  环境配置文件 .env.$ENV_ARG 不存在，使用默认配置"
fi
set +a

# 设置默认值
APP_PORT=${APP_PORT:-8000}
APP_ENV=${APP_ENV:-$ENV_ARG}

echo "🚀 Using uv to start FastAPI in $APP_ENV mode on port $APP_PORT..."

# 使用 uv 启动 uvicorn
# --reload 仅在非生产环境下开启
if [ "$APP_ENV" == "pro" ]; then
    uv run uvicorn app.main:app --host 0.0.0.0 --port $APP_PORT
else
    uv run uvicorn app.main:app --host 127.0.0.1 --port $APP_PORT --reload
fi
