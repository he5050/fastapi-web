from typing import Optional
from pydantic import EmailStr, Field
from datetime import datetime
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """
    用户基础 Schema
    """

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """
    用户创建 Schema
    """

    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseSchema):
    """
    用户更新 Schema
    """

    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    password: Optional[str] = Field(None, min_length=6, description="新密码")
    is_active: Optional[bool] = None


class UserOut(UserBase):
    """
    用户详情输出 Schema
    """

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
