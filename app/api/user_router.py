from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.core.response import BaseResponse, PageData, PageResponse
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user_model import User
from app.schemas.base_schema import PaginationParams
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post("/add", response_model=BaseResponse[UserOut], summary="新增用户")
async def create_user(
    obj_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[UserOut]:
    service = UserService(db)
    user = await service.create_user(obj_in)
    # 新增用户后，清空用户列表缓存
    await FastAPICache.clear(namespace="users_list")
    return BaseResponse.success_res(data=user)


@router.get("/list", response_model=PageResponse[UserOut], summary="获取用户列表")
@cache(namespace="users_list", expire=60)
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PageResponse[UserOut]:
    """
    获取用户列表，参数由 FastAPI 自动验证
    """
    service = UserService(db)
    data = await service.list_users(pagination.page, pagination.page_size)
    page_data = PageData[UserOut](**data)
    return PageResponse(success=True, data=page_data, message="获取成功")


@router.get(
    "/detail/{user_id}", response_model=BaseResponse[UserOut], summary="获取用户详情"
)
@cache(namespace="user_detail", expire=300)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[UserOut]:
    service = UserService(db)
    user = await service.get_user(user_id)
    return BaseResponse.success_res(data=user)


@router.put(
    "/update/{user_id}", response_model=BaseResponse[UserOut], summary="更新用户"
)
async def update_user(
    user_id: int,
    obj_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[UserOut]:
    service = UserService(db)
    user = await service.update_user(user_id, obj_in)
    # 更新用户信息后，清空相关缓存
    await FastAPICache.clear(namespace="user_detail")
    await FastAPICache.clear(namespace="users_list")
    return BaseResponse.success_res(data=user)


@router.delete(
    "/delete/{user_id}", response_model=BaseResponse[Any], summary="删除用户"
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[Any]:
    service = UserService(db)
    await service.delete_user(user_id)
    # 删除用户后，清空相关缓存
    await FastAPICache.clear(namespace="user_detail")
    await FastAPICache.clear(namespace="users_list")
    return BaseResponse.success_res(message="用户删除成功")
