from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.core.response import BaseResponse, PageData, PageResponse
from app.core.security import get_current_active_user
from app.core.permissions import require_self_or_admin, require_admin
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
    # 使用权限控制方法创建用户输出对象
    user_out = UserOut.from_user_with_permission(user, current_user)
    # 新增用户后，清空用户列表缓存
    await FastAPICache.clear(namespace="users_list")
    return BaseResponse.success_res(data=user_out)


@router.get("/list", response_model=PageResponse[UserOut], summary="获取用户列表")
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PageResponse[UserOut]:
    """
    获取用户列表，参数由 FastAPI 自动验证
    """
    service = UserService(db)
    # 传递current_user参数进行权限过滤
    data = await service.list_users(pagination.page, pagination.page_size, current_user)
    # 使用权限控制方法创建用户输出列表
    user_out_list = [UserOut.from_user_with_permission(user, current_user) for user in data["records"]]
    data["records"] = user_out_list
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
    
    # 检查查看权限
    if not await service.can_view_user(current_user, user_id):
        return BaseResponse.fail_res(message="没有权限查看该用户信息")
        
    user = await service.get_user(user_id)
    # 使用权限控制方法创建用户输出对象，确保缓存能正确序列化
    user_out = UserOut.from_user_with_permission(user, current_user)
    return BaseResponse.success_res(data=user_out)


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
    
    # 检查更新权限
    if not await service.can_update_user(current_user, user_id):
        return BaseResponse.fail_res(message="没有权限修改该用户信息")
        
    user = await service.update_user(user_id, obj_in)
    # 使用权限控制方法创建用户输出对象
    user_out = UserOut.from_user_with_permission(user, current_user)
    # 更新用户信息后，清空相关缓存
    await FastAPICache.clear(namespace="user_detail")
    await FastAPICache.clear(namespace="users_list")
    return BaseResponse.success_res(data=user_out)


@router.delete(
    "/delete/{user_id}", response_model=BaseResponse[Any], summary="删除用户"
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BaseResponse[Any]:
    service = UserService(db)
    
    # 检查删除权限
    if not await service.can_delete_user(current_user, user_id):
        return BaseResponse.fail_res(message="没有权限删除该用户")
        
    await service.delete_user(user_id)
    # 删除用户后，清空相关缓存
    await FastAPICache.clear(namespace="user_detail")
    await FastAPICache.clear(namespace="users_list")
    return BaseResponse.success_res(message="用户删除成功")
