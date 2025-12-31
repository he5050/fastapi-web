import re
from typing import Any

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate


class UserService:
    """
    用户业务逻辑层
    """

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    def _hash_password(self, password: str) -> str:
        """使用bcrypt进行安全密码哈希"""
        # bcrypt只支持72字节以内的密码，需要截断
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # 生成盐值并哈希
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        # bcrypt只支持72字节以内的密码，需要截断
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        hashed_bytes = hashed_password.encode("utf-8")

        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def _validate_password_strength(self, password: str) -> None:
        """验证密码强度"""
        if len(password) < 8:
            raise AppError("密码长度至少8位")
        if not any(c.isupper() for c in password):
            raise AppError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in password):
            raise AppError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in password):
            raise AppError("密码必须包含至少一个数字")
        # 检查是否包含特殊字符
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise AppError("密码必须包含至少一个特殊字符")
        # 检查是否包含常见弱密码模式（使用更精确的匹配）
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
            if re.search(pattern, password, re.IGNORECASE):
                raise AppError("密码不能包含常见的弱密码模式")

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AppError(f"用户 ID {user_id} 不存在")
        return user

    async def list_users(self, page: int, page_size: int) -> dict[str, Any]:
        items, total = await self.repo.get_list(page, page_size)
        total_page = (total + page_size - 1) // page_size
        return {
            "records": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_page": total_page,
        }

    async def create_user(self, obj_in: UserCreate) -> User:
        # 1. 验证密码强度
        self._validate_password_strength(obj_in.password)

        # 2. 检查用户名唯一性
        existing_user = await self.repo.get_by_user_name(obj_in.user_name)
        if existing_user:
            raise AppError(f"用户名 {obj_in.user_name} 已存在")

        # 3. 检查邮箱唯一性 (如果提供了邮箱)
        if obj_in.email:
            existing_email = await self.repo.get_by_email(obj_in.email)
            if existing_email:
                raise AppError(f"邮箱 {obj_in.email} 已被注册")

        user_data = obj_in.model_dump()
        password = user_data.pop("password")
        user_data["hashed_password"] = self._hash_password(password)
        user_data["user_type"] = 9  # 强制设置为普通用户

        db_user = User(**user_data)
        return await self.repo.create(db_user)

    async def update_user(self, user_id: int, obj_in: UserUpdate) -> User:
        await self.get_user(user_id)  # 确保存在
        update_data = obj_in.model_dump(exclude_unset=True)
        result = await self.repo.update(user_id, update_data)
        if result is None:
            raise AppError(f"用户 ID {user_id} 更新失败")
        return result

    async def delete_user(self, user_id: int) -> bool:
        await self.get_user(user_id)  # 确保存在
        return await self.repo.delete(user_id)