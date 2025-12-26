from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from app.core.response import BaseResponse


class AppError(Exception):
    """
    业务逻辑异常基类
    """

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


async def global_exception_handler(_request: Request, exc: Exception):
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
    elif hasattr(exc, "errors"):
        # Pydantic 验证异常 (RequestValidationError)
        # 获取第一个错误信息作为提示
        errors = getattr(exc, "errors")()
        first_error = errors[0] if errors else {}

        # 优化错误消息展示
        msg = first_error.get("msg", "参数验证失败")
        if "Value error, " in msg:
            msg = msg.replace("Value error, ", "")

        field = ".".join([str(l) for l in first_error.get("loc", []) if l != "body"])

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=BaseResponse.fail_res(
                message=f"{field}参数错误: {msg}"
            ).model_dump(),
        )
    else:
        # 系统未知异常
        print(f"系统异常: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=BaseResponse.fail_res(message="服务器内部错误").model_dump(),
        )
