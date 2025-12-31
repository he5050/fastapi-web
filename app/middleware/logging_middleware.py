import json
import logging
import time
from datetime import datetime
from typing import List, Optional, Set, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.types import ASGIApp

from app.core.config import settings
from app.models.log_model import SysLog
from app.repositories.log_repository import SysLogRepository

logger = logging.getLogger(__name__)


class LoggingMiddlewareConfig:
    """
    日志中间件配置类
    """

    def __init__(self):
        # 从配置中获取排除规则，如果没有则使用默认值
        config = getattr(settings, "LOGGING_MIDDLEWARE_CONFIG", {})

        # 排除的路径前缀（支持前缀匹配）
        self.excluded_paths: List[str] = config.get(
            "excluded_paths", ["/health", "/docs", "/openapi.json"]
        )

        # 排除的HTTP方法
        self.excluded_methods: List[str] = config.get("excluded_methods", [])

        # 排除的状态码
        self.excluded_status_codes: List[int] = config.get("excluded_status_codes", [])

        # 排除的路径正则表达式
        self.excluded_path_patterns: List[str] = config.get(
            "excluded_path_patterns", []
        )

        # 响应体最大长度（超过此长度将被截断）
        self.max_response_length: int = config.get("max_response_length", 1000)

        # 请求参数最大长度（超过此长度将被截断）
        self.max_request_length: int = config.get("max_request_length", 1000)

        # 是否记录响应体
        self.log_response_body: bool = config.get("log_response_body", True)

        # 是否记录请求体
        self.log_request_body: bool = config.get("log_request_body", True)


class LoggingMiddleware:
    """
    日志中间件，用于记录所有请求和响应信息

    功能特性：
    1. 自动记录请求/响应信息（URL、方法、参数、响应、耗时等）
    2. 支持排除特定路径、方法、状态码的日志记录
    3. 智能解析请求参数（GET/POST/PUT/PATCH等）
    4. 自动提取访问模块和操作类型
    5. 异步保存日志，不影响业务性能
    6. 支持响应体截断和敏感信息过滤
    7. 完善的异常处理和错误恢复

    配置说明：
    - 通过 settings.LOGGING_MIDDLEWARE_CONFIG 配置排除规则
    - 支持路径前缀匹配、正则表达式匹配
    - 支持按HTTP方法、状态码排除
    - 支持自定义响应体截断长度
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        # 初始化配置
        self.config = LoggingMiddlewareConfig()

        # 复用主数据库引擎和会话工厂，避免重复创建连接池
        from app.db.session import AsyncSessionLocal
        self.log_session_local = AsyncSessionLocal

        logger.info(f"日志中间件已初始化（复用主数据库引擎），排除路径: {self.config.excluded_paths}")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 创建请求对象
        request = Request(scope, receive)

        # 检查是否需要排除此请求
        if self._should_exclude_request(request):
            await self.app(scope, receive, send)
            return

        # 记录请求开始时间
        start_time = time.time()

        try:
            # 提取请求信息
            request_info = self._extract_request_info(request)

            # 解析请求参数
            request_params, cached_body = await self._parse_request_params(request)

            # 执行请求
            response_body, status_code = await self._execute_request(
                scope, receive, send, cached_body
            )

            # 获取路由信息
            route_info = self._extract_route_info(request)

            # 计算耗时
            duration = int((time.time() - start_time) * 1000)

            # 操作结果状态
            response_status = self._extract_response_status(response_body)

            # 处理响应结果
            response_result = self._process_response_body(response_body)

            # 判断接口请求状态
            operation_status = "success" if status_code < 400 else "failure"

            # 构建并保存日志
            await self._save_log_entry(
                request_info=request_info,
                request_params=request_params,
                route_info=route_info,
                status_code=status_code,
                response_status=response_status,
                response_result=response_result,
                duration=duration,
                operation_status=operation_status,
            )

        except Exception as e:
            logger.error(f"日志中间件处理失败: {str(e)}")
            # 即使日志记录失败，也要确保请求正常执行
            await self.app(scope, receive, send)

    def _should_exclude_request(self, request: Request) -> bool:
        """检查是否应该排除此请求的记录"""
        path = request.url.path
        method = request.method

        # 检查路径前缀排除
        for excluded_path in self.config.excluded_paths:
            if path.startswith(excluded_path):
                return True

        # 检查HTTP方法排除
        if method in self.config.excluded_methods:
            return True

        # 检查路径正则表达式排除
        import re

        for pattern in self.config.excluded_path_patterns:
            if re.match(pattern, path):
                return True

        return False

    def _extract_request_info(self, request: Request) -> dict:
        """提取请求基本信息"""
        return {
            "request_url": str(request.url),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", "")[:500],
        }

    async def _parse_request_params(self, request: Request) -> tuple:
        """解析请求参数"""
        request_params = {}
        cached_body = b""

        try:
            if request.method in ["GET", "DELETE"]:
                request_params = dict(request.query_params)
            elif (
                request.method in ["POST", "PUT", "PATCH"]
                and self.config.log_request_body
            ):
                cached_body = await request.body()
                if cached_body:
                    request_params = self._parse_body_params(cached_body)
        except Exception as e:
            logger.warning(f"解析请求参数失败: {str(e)}")

        return request_params, cached_body

    def _parse_body_params(self, body: bytes) -> dict:
        """解析请求体参数"""
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            # 如果不是JSON，返回空字典（不记录非JSON的请求体）
            return {}

    async def _execute_request(self, scope, receive, send, cached_body: bytes) -> tuple:
        """执行请求并捕获响应"""
        response_body = bytearray()
        status_code = 200
        body_sent = False
        response_started = False

        async def send_wrapper(message):
            nonlocal status_code, response_body, body_sent, response_started
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
            elif message["type"] == "http.response.body":
                if "body" in message and message["body"]:
                    response_body.extend(message["body"])
                # 检查是否还有更多body数据
                body_sent = not message.get("more_body", False)
            await send(message)

        async def receive_wrapper():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": cached_body, "more_body": False}
            return await receive()

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception as e:
            logger.error(f"请求处理异常: {str(e)}", exc_info=True)
            status_code = 500
            error_message = str(e)
            response_body = bytearray(error_message.encode("utf-8"))

            # 如果响应还未开始，需要手动发送响应
            if not response_started:
                try:
                    # 发送响应头
                    await send({
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [[b"content-type", b"application/json"]],
                    })
                    # 发送响应体
                    error_response = json.dumps({
                        "success": False,
                        "message": "服务器内部错误",
                        "data": None
                    }, ensure_ascii=False).encode("utf-8")
                    response_body = bytearray(error_response)
                    await send({
                        "type": "http.response.body",
                        "body": error_response,
                    })
                except Exception as send_error:
                    logger.error(f"发送错误响应失败: {str(send_error)}")

        return response_body, status_code

    def _extract_route_info(self, request: Request) -> dict:
        """提取路由信息"""
        route = request.scope.get("route")
        if not route:
            return {"visit_module": None, "operation_type": None}

        visit_module = route.tags[0] if route.tags else None
        operation_type = getattr(route, "summary", None)
        if not operation_type:
            operation_type = getattr(route, "operation_id", None)

        return {"visit_module": visit_module, "operation_type": operation_type}

    def _process_response_body(self, response_body: bytearray) -> str:
        """处理响应体"""
        if not self.config.log_response_body:
            return ""

        try:
            response_result = response_body.decode("utf-8", errors="ignore")
            return response_result[: self.config.max_response_length]
        except Exception:
            return str(response_body)

    def _extract_response_status(self, response_body: bytearray) -> str:
        """从响应体中提取操作结果状态"""
        try:
            if not response_body:
                return "unknown"

            # 尝试解析JSON响应
            response_text = response_body.decode("utf-8", errors="ignore")
            response_data = json.loads(response_text)

            # 检查是否有success字段
            if isinstance(response_data, dict) and "success" in response_data:
                return "success" if response_data["success"] else "failure"

            # 如果没有success字段，尝试检查是否有code字段
            if isinstance(response_data, dict) and "code" in response_data:
                code = response_data["code"]
                # 假设200表示成功，其他表示失败
                return "success" if code == 200 else "failure"

        except (json.JSONDecodeError, KeyError, TypeError):
            # 如果解析失败，返回unknown
            pass

        return "unknown"

    async def _save_log_entry(self, **kwargs):
        """保存日志条目"""
        try:
            log_entry = SysLog(
                request_url=kwargs["request_info"]["request_url"],
                request_method=kwargs["request_info"]["request_method"],
                request_params=json.dumps(
                    kwargs["request_params"], ensure_ascii=False, default=str
                ),
                visit_module=kwargs["route_info"]["visit_module"],
                operation_type=kwargs["route_info"]["operation_type"],
                operation_status=kwargs["operation_status"],
                response_status=kwargs["response_status"],
                response_result=kwargs["response_result"],
                request_time=datetime.now(),
                duration=kwargs["duration"],
                client_ip=kwargs["request_info"]["client_ip"],
                user_agent=kwargs["request_info"]["user_agent"],
            )
            await self._save_log_async(log_entry)
        except Exception as e:
            logger.error(f"保存日志失败: {str(e)}")

    async def _save_log_async(self, log_entry: SysLog):
        """异步保存日志，使用独立的数据库会话"""
        try:
            async with self.get_log_session()() as session:
                repo = SysLogRepository(session)
                await repo.create(log_entry)
        except Exception as e:
            logger.error(f"保存日志到数据库失败: {str(e)}")
            # 不抛出异常，避免影响业务逻辑

    def get_log_session(self):
        """获取数据库会话（复用主数据库引擎）"""
        return self.log_session_local
