from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import BaseResponse


class AppError(Exception):
    """
    业务逻辑异常基类
    """

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


def get_http_status_message(status_code: int, detail: str = "") -> str:
    """
    获取HTTP状态码对应的错误消息
    """
    status_messages = {
        # 3xx 重定向
        301: "资源已永久移动",
        302: "资源已临时移动",
        304: "资源未修改",
        # 4xx 客户端错误
        400: "请求参数错误",
        401: "未授权访问，请先登录",
        403: "权限不足，无法访问该资源",
        404: "请求的资源不存在",
        405: "请求方法不被允许",
        408: "请求超时",
        409: "资源冲突",
        410: "资源已永久删除",
        413: "请求实体过大",
        414: "请求URI过长",
        415: "不支持的媒体类型",
        422: "请求参数验证失败",
        429: "请求过于频繁，请稍后再试",
        # 5xx 服务器错误
        500: "服务器内部错误",
        502: "网关错误",
        503: "服务暂不可用",
        504: "网关超时",
    }

    default_message = status_messages.get(status_code, f"HTTP {status_code} 错误")

    if detail:
        return f"{default_message}: {detail}"
    return default_message


def handle_starlette_exception(exc: StarletteHTTPException) -> JSONResponse:
    """
    处理Starlette HTTP异常
    """
    status_code = exc.status_code
    message = get_http_status_message(status_code, exc.detail or "")

    # 对于重定向类状态码（3xx），保持原始状态码
    if 300 <= status_code < 400:
        return JSONResponse(
            status_code=status_code,
            content=BaseResponse.fail_res(message=message).model_dump(),
        )
    else:
        # 其他错误状态码统一返回200，便于前端处理
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=BaseResponse.fail_res(message=message).model_dump(),
        )


def handle_validation_exception(exc) -> JSONResponse:
    """
    处理Pydantic验证异常
    """
    errors = getattr(exc, "errors")()
    first_error = errors[0] if errors else {}

    msg = first_error.get("msg", "参数验证失败")
    if "Value error, " in msg:
        msg = msg.replace("Value error, ", "")

    field = ".".join([str(l) for l in first_error.get("loc", []) if l != "body"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=BaseResponse.fail_res(
            message=f"【{field}】参数错误: {msg}"
        ).model_dump(),
    )


def global_exception_handler(_request: Request, exc: Exception):
    """
    全局异常捕获
    """
    if isinstance(exc, AppError):
        # 业务逻辑异常
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=BaseResponse.fail_res(message=exc.message).model_dump(),
        )
    elif isinstance(exc, HTTPException):
        # FastAPI 自带异常
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseResponse.fail_res(message=exc.detail).model_dump(),
        )
    elif isinstance(exc, StarletteHTTPException):
        # Starlette HTTP 异常（包括301、401、403、404、500等）
        return handle_starlette_exception(exc)
    elif hasattr(exc, "errors"):
        # Pydantic 验证异常 (RequestValidationError)
        return handle_validation_exception(exc)
    else:
        # 系统未知异常
        print(f"系统异常: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=BaseResponse.fail_res(message="服务器内部错误").model_dump(),
        )
