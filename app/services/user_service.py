import re
from typing import Any, Optional

from passlib.hash import pbkdf2_sha256
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
        """使用PBKDF2进行安全密码哈希"""
        return pbkdf2_sha256.hash(password, rounds=100000)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pbkdf2_sha256.verify(plain_password, hashed_password)

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

    async def list_users(self, page: int, page_size: int, current_user: Optional[User] = None) -> dict[str, Any]:
        items, total = await self.repo.get_list(page, page_size, current_user)
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

    async def can_delete_user(self, current_user: User, target_user_id: int) -> bool:
        """检查当前用户是否可以删除目标用户"""
        # 只有管理员可以删除用户
        if current_user.user_type != 1:
            return False
            
        # 获取目标用户
        target_user = await self.get_user(target_user_id)
        
        # 不能删除自己
        if target_user.user_id == current_user.user_id:
            raise AppError("不能删除自己的账户")
            
        return True

    async def can_view_user(self, current_user: User, target_user_id: int) -> bool:
        """检查当前用户是否可以查看目标用户"""
        # 管理员可以查看所有用户
        if current_user.user_type == 1:
            return True
            
        # 普通用户只能查看自己
        if current_user.user_id == target_user_id:
            return True
            
        return False

    async def can_update_user(self, current_user: User, target_user_id: int) -> bool:
        """检查当前用户是否可以更新目标用户"""
        # 获取目标用户
        target_user = await self.get_user(target_user_id)
        
        # 管理员可以更新所有用户（但不能修改其他管理员的信息）
        if current_user.user_type == 1:
            # 如果目标用户是管理员且不是自己，限制部分操作
            if target_user.user_type == 1 and target_user.user_id != current_user.user_id:
                raise AppError("不能修改其他管理员用户的信息")
            return True
            
        # 普通用户不能修改管理员用户
        if target_user.user_type == 1:
            return False
            
        # 普通用户只能修改自己
        if current_user.user_id == target_user_id:
            return True
            
        return False
