from datetime import datetime
from typing import Any, Optional

from pydantic import EmailStr, Field, field_validator, field_serializer

from app.core.validator import ValidationRule, validate_rules
from app.schemas.base_schema import BaseSchema


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
        import re

        rules = [
            ValidationRule(required=True, message="请输入密码"),
            ValidationRule(min_len=8, message="密码长度至少8位"),
            ValidationRule(max_len=128, message="密码长度不能超过128位"),
        ]

        # 基础规则验证
        v = validate_rules(v, rules)

        # 密码强度验证
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("密码必须包含至少一个特殊字符")

        # 检查常见弱密码模式（使用更精确的匹配）
        weak_patterns = [
            r"^123456",
            r"^password",
            r"^admin",
            r"^qwerty",
            r"^abc123",
            r"^111111",
            r"^000000",
        ]
        for pattern in weak_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("密码不能包含常见的弱密码模式")

        return v


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

    user_name: str
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_type: int
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """将datetime对象格式化为YYYY-MM-DD HH:mm:ss格式"""
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")
