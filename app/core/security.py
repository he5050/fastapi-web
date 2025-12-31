"""
安全工具类：JWT token管理和密码验证
"""

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_service import redis_service
from app.db.session import get_db
from app.models.user_model import User
from app.repositories.user_repository import UserRepository

# OAuth2密码Bearer模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码

    Returns:
        bool: 密码是否匹配
    """
    # bcrypt只支持72字节以内的密码，需要截断
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    hashed_bytes = hashed_password.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问token

    Args:
        data: 要编码的数据字典（必须包含sub字段作为用户ID）
        expires_delta: 自定义过期时间，如果未指定则使用配置的默认值

    Returns:
        str: JWT token字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新token

    Args:
        data: 要编码的数据字典（必须包含sub字段作为用户ID）

    Returns:
        str: JWT token字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    解码token

    Args:
        token: JWT token字符串

    Returns:
        dict: 解码后的token payload

    Raises:
        HTTPException: 当token无效或过期时抛出401错误
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户（依赖注入函数）

    Args:
        token: 从Authorization header中提取的Bearer token
        db: 数据库会话

    Returns:
        User: 当前登录的用户对象

    Raises:
        HTTPException: 当token无效、过期或用户不存在时抛出401错误
    
    说明：会从Redis中验证token的有效性（支持单点登录）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 从Redis中验证token是否有效（支持单点登录）
    redis_user_id = redis_service.get_user_id_by_access_token(token)
    if redis_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期或已失效（可能被重新登录撤销）",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    token_type: str = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token类型",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证token中的user_id与Redis中存储的一致
    if str(redis_user_id) != user_id:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id))
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户（依赖注入函数）

    Args:
        current_user: 当前登录的用户对象

    Returns:
        User: 活跃的用户对象

    Raises:
        HTTPException: 当用户未激活时抛出400错误
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user