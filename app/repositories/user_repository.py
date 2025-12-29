from typing import Any, List, Optional, Tuple

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User


class UserRepository:
    """
    用户数据访问层
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.user_id == user_id, User.is_deleted == False)
        )
        return result.scalars().first()

    async def get_by_user_name(self, user_name: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.user_name == user_name, User.is_deleted == False)
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalars().first()

    async def get_list(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[List[User], int]:
        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询总数
        count_result = await self.db.execute(
            select(func.count(User.user_id)).where(User.is_deleted == False)
        )
        total = count_result.scalar() or 0

        # 查询列表
        result = await self.db.execute(
            select(User)
            .where(User.is_deleted == False)
            .offset(offset)
            .limit(page_size)
            .order_by(User.user_id.desc())
        )
        items = result.scalars().all()
        return list(items), total

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, obj_in: dict[str, Any]) -> Optional[User]:
        await self.db.execute(
            update(User).where(User.user_id == user_id).values(**obj_in)
        )
        await self.db.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        # 软删除
        result = await self.db.execute(
            update(User).where(User.user_id == user_id).values(is_deleted=True)
        )
        await self.db.commit()
        # SQLAlchemy 异步执行返回的 result 对象中包含 rowcount
        rowcount = getattr(result, "rowcount", 0)
        return bool(rowcount)
