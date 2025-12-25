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


async def global_exception_handler(request: Request, exc: Exception):
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
    else:
        # 系统未知异常
        print(f"系统异常: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=BaseResponse.fail_res(message="服务器内部错误").model_dump(),
        )
