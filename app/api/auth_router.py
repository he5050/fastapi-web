"""
认证相关路由：登录、刷新token、获取当前用户信息
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import BaseResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    verify_password,
)
from app.core.redis_service import redis_service
from app.core.config import settings
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, TokenRefreshRequest, TokenResponse
from app.schemas.user_schema import UserOut

router = APIRouter(prefix="/auth", tags=["认证管理"])


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[dict]:
    """
    用户登出，撤销当前用户的所有token

    说明：
    - 撤销用户的所有访问token和刷新token
    - 实现单点登录，用户在任意位置登出，所有设备都会失效
    """
    # 撤销用户的所有token
    redis_service.revoke_all_user_tokens(current_user.user_id)

    return BaseResponse.success_res(message="登出成功")


@router.post("/login", response_model=BaseResponse[TokenResponse], summary="用户登录")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[TokenResponse]:
    """
    用户登录，返回访问token和刷新token

    - **username**: 用户名
    - **password**: 密码

    返回：
    - **access_token**: 访问token，用于API请求认证
    - **refresh_token**: 刷新token，用于获取新的访问token
    - **token_type**: token类型，固定为bearer
    - **expires_in**: 访问token过期时间（秒）

    说明：实现单点登录，同一用户重新登录会撤销之前的token
    """
    repo = UserRepository(db)

    # 查找用户
    user = await repo.get_by_user_name(request.username)
    if not user:
        return BaseResponse.fail_res(message="用户名或密码错误")

    # 验证密码
    if not verify_password(request.password, user.hashed_password):
        return BaseResponse.fail_res(message="用户名或密码错误")

    if not user.is_active:
        return BaseResponse.fail_res(message="用户已被禁用")

    # 实现单点登录：撤销用户之前的所有token
    redis_service.revoke_all_user_tokens(user.user_id)

    # 生成新的token
    access_token = create_access_token(data={"sub": str(user.user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user.user_id)})

    # 将token存储到Redis
    redis_service.store_access_token(
        user_id=user.user_id,
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    redis_service.store_refresh_token(user_id=user.user_id, refresh_token=refresh_token)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return BaseResponse.success_res(data=token_response, message="登录成功")


@router.post(
    "/refresh", response_model=BaseResponse[TokenResponse], summary="刷新token"
)
async def refresh_token(
    request: TokenRefreshRequest,
) -> BaseResponse[TokenResponse]:
    """
    使用刷新token获取新的访问token

    - **refresh_token**: 刷新token

    当访问token过期时，可以使用此接口获取新的访问token，
    而无需重新登录。

    说明：会从Redis中验证刷新token的有效性
    """
    from app.core.security import decode_token

    # 从Redis中验证刷新token
    user_id = redis_service.get_user_id_by_refresh_token(request.refresh_token)
    if user_id is None:
        return BaseResponse.fail_res(message="刷新token已过期或无效")

    # 生成新的访问token
    access_token = create_access_token(data={"sub": str(user_id)})

    # 将新的访问token存储到Redis
    redis_service.store_access_token(
        user_id=user_id,
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 刷新token不变
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return BaseResponse.success_res(data=token_response, message="刷新成功")


@router.get("/me", response_model=BaseResponse[UserOut], summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[UserOut]:
    """
    获取当前登录用户信息

    需要在请求头中携带有效的访问token：
    ```
    Authorization: Bearer <access_token>
    ```
    """

    user_out = UserOut.model_validate(current_user)

    return BaseResponse.success_res(data=user_out, message="获取用户信息成功")
