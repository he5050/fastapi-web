from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sys_log_model import SysLog


class SysLogRepository:
    """
    系统日志数据访问层
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, log: SysLog) -> SysLog:
        """
        创建系统日志记录
        
        Args:
            log: 系统日志对象
            
        Returns:
            创建的系统日志对象
        """
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log