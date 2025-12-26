from typing import Optional, Any
from pydantic import EmailStr, Field, field_validator
from datetime import datetime
from app.schemas.base_schema import BaseSchema


from app.core.validator import ValidationRule, validate_rules


class UserBase(BaseSchema):
    """
    用户基础 Schema
    """

    user_name: str = Field(..., max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """
    用户创建 Schema
    """

    password: str = Field(..., description="密码")

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, v: str) -> Any:
        rules = [
            ValidationRule(required=True, message="请输入用户名"),
            ValidationRule(min_len=3, message="用户名长度不能少于 3 个字符"),
        ]
        return validate_rules(v, rules)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> Any:
        rules = [
            ValidationRule(required=True, message="请输入密码"),
            ValidationRule(min_len=6, message="密码长度不能少于 6 个字符"),
        ]
        return validate_rules(v, rules)


class UserUpdate(BaseSchema):
    """
    用户更新 Schema
    """

    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserOut(UserBase):
    """
    用户详情输出 Schema
    """

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
