"""
认证相关的 Schema 定义
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(..., description="访问token")
    refresh_token: str = Field(..., description="刷新token")
    token_type: str = Field(default="bearer", description="token类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class TokenRefreshRequest(BaseModel):
    """刷新token请求"""
    refresh_token: str = Field(..., description="刷新token")