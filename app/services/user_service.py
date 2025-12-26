from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user_model import User
from app.core.exceptions import AppError
import hashlib


class UserService:
    """
    用户业务逻辑层
    """

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    def _hash_password(self, password: str) -> str:
        """简单的哈希处理 (实际项目建议用 passlib)"""
        return hashlib.sha256(password.encode()).hexdigest()

    async def get_user(self, user_id: int):
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AppError(f"用户 ID {user_id} 不存在")
        return user

    async def list_users(self, page: int, size: int):
        items, total = await self.repo.get_list(page, size)
        total_page = (total + size - 1) // size
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "total_page": total_page,
        }

    async def create_user(self, obj_in: UserCreate):
        # 1. 检查用户名唯一性
        existing_user = await self.repo.get_by_user_name(obj_in.user_name)
        if existing_user:
            raise AppError(f"用户名 {obj_in.user_name} 已存在")

        # 2. 检查邮箱唯一性 (如果提供了邮箱)
        if obj_in.email:
            existing_email = await self.repo.get_by_email(obj_in.email)
            if existing_email:
                raise AppError(f"邮箱 {obj_in.email} 已被注册")

        user_data = obj_in.model_dump()
        password = user_data.pop("password")
        user_data["hashed_password"] = self._hash_password(password)

        db_user = User(**user_data)
        return await self.repo.create(db_user)

    async def update_user(self, user_id: int, obj_in: UserUpdate):
        await self.get_user(user_id)  # 确保存在

        update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            password = update_data.pop("password")
            update_data["hashed_password"] = self._hash_password(password)

        return await self.repo.update(user_id, update_data)

    async def delete_user(self, user_id: int):
        await self.get_user(user_id)  # 确保存在
        return await self.repo.delete(user_id)
