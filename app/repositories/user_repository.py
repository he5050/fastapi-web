from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.models.user_model import User
from typing import List, Optional, Tuple


class UserRepository:
    """
    用户数据访问层
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username, User.is_deleted == False)
        )
        return result.scalars().first()

    async def get_list(self, page: int = 1, size: int = 10) -> Tuple[List[User], int]:
        # 计算偏移量
        offset = (page - 1) * size

        # 查询总数
        count_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_deleted == False)
        )
        total = count_result.scalar() or 0

        # 查询列表
        result = await self.db.execute(
            select(User)
            .where(User.is_deleted == False)
            .offset(offset)
            .limit(size)
            .order_by(User.id.desc())
        )
        items = result.scalars().all()
        return list(items), total

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, obj_in: dict) -> Optional[User]:
        await self.db.execute(update(User).where(User.id == user_id).values(**obj_in))
        await self.db.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        # 软删除
        result = await self.db.execute(
            update(User).where(User.id == user_id).values(is_deleted=True)
        )
        await self.db.commit()
        return result.rowcount > 0
