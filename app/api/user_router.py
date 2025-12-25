from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.response import BaseResponse, PageResponse
from typing import List

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post("/add", response_model=BaseResponse[UserOut], summary="创建用户")
async def create_user(obj_in: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.create_user(obj_in)
    return BaseResponse.success_res(data=user)


@router.get("/list", response_model=PageResponse[UserOut], summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    data = await service.list_users(page, size)
    return BaseResponse.success_res(data=data)


@router.get(
    "/detail/{user_id}", response_model=BaseResponse[UserOut], summary="获取用户详情"
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.get_user(user_id)
    return BaseResponse.success_res(data=user)


@router.put(
    "/update/{user_id}", response_model=BaseResponse[UserOut], summary="更新用户"
)
async def update_user(
    user_id: int, obj_in: UserUpdate, db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    user = await service.update_user(user_id, obj_in)
    return BaseResponse.success_res(data=user)


@router.delete("/delete/{user_id}", response_model=BaseResponse, summary="删除用户")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    await service.delete_user(user_id)
    return BaseResponse.success_res(message="用户删除成功")
