import time
import json
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Optional
from app.models.sys_log_model import SysLog
from app.repositories.sys_log_repository import SysLogRepository
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    日志中间件，用于记录所有请求和响应信息
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        # 创建独立的数据库引擎用于日志写入
        self.log_engine = create_async_engine(
            settings.async_database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.LogSessionLocal = async_sessionmaker(
            bind=self.log_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 创建请求对象
        request = Request(scope, receive)

        # 记录请求开始时间
        start_time = time.time()

        # 不记录健康检查接口的日志
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return

        # 提取请求信息
        request_url = str(request.url)
        request_method = request.method
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        # 解析请求参数
        request_params = {}
        try:
            if request_method in ["GET", "DELETE"]:
                request_params = dict(request.query_params)
            elif request_method in ["POST", "PUT", "PATCH"]:
                # 尝试读取JSON body
                body = await request.body()
                if body:
                    try:
                        request_params = await request.json()
                    except:
                        # 如果不是JSON，尝试form data
                        try:
                            request_params = await request.form()
                            request_params = dict(request_params)
                        except:
                            pass
        except Exception as e:
            logger.warning(f"解析请求参数失败: {str(e)}")

        # 获取路由信息（访问模块和操作类型）
        route = request.scope.get("route")
        visit_module = None
        operation_type = None
        if route:
            # 从 tags 中获取访问模块
            visit_module = route.tags[0] if route.tags else None
            # 从 summary 中获取操作类型（如"新增用户"、"获取用户列表"等）
            operation_type = getattr(route, "summary", None)
            # 如果 summary 不存在，尝试使用 operation_id（函数名）
            if not operation_type:
                operation_type = getattr(route, "operation_id", None)

        # 存储原始send函数
        response_body = bytearray()
        status_code = 200

        async def send_wrapper(message):
            nonlocal status_code, response_body
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                if "body" in message and message["body"]:
                    response_body.extend(message["body"])
            await send(message)

        # 执行请求
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # 如果请求过程中发生异常，记录异常信息
            logger.error(f"请求处理异常: {str(e)}")
            status_code = 500
            response_body = str(e).encode("utf-8")

        # 计算耗时
        duration = int((time.time() - start_time) * 1000)

        # 读取响应内容
        response_result = ""
        try:
            response_result = response_body.decode("utf-8", errors="ignore")
        except:
            response_result = str(response_body)

        # 判断操作结果（根据状态码）
        operation_status = "success" if status_code < 400 else "failure"

        # 构建日志对象
        log_entry = SysLog(
            request_url=request_url,
            request_method=request_method,
            request_params=json.dumps(request_params, ensure_ascii=False, default=str),
            visit_module=visit_module,
            operation_type=operation_type,
            operation_status=operation_status,
            response_result=response_result[:1000],  # 限制长度
            request_time=datetime.now(),
            duration=duration,
            client_ip=client_ip,
            user_agent=user_agent[:500] if user_agent else None,
        )

        # 异步保存日志（不阻塞响应）
        try:
            await self._save_log_async(log_entry)
        except Exception as e:
            # 日志保存失败不应影响业务，仅记录错误
            logger.error(f"保存日志失败: {str(e)}")

    async def _save_log_async(self, log_entry: SysLog):
        """异步保存日志，使用独立的数据库会话"""
        try:
            async with self.LogSessionLocal() as session:
                repo = SysLogRepository(session)
                await repo.create(log_entry)
        except Exception as e:
            logger.error(f"保存日志到数据库失败: {str(e)}")
            raise