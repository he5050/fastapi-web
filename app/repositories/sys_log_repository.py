from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
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

    async def get_list(
        self, 
        page: int, 
        page_size: int, 
        filters: Optional[dict] = None
    ) -> Tuple[List[SysLog], int]:
        """
        分页查询日志列表
        
        Args:
            page: 页码
            page_size: 每页数量
            filters: 过滤条件
            
        Returns:
            日志列表和总数量
        """
        query = select(SysLog)
        
        # 构建过滤条件
        if filters:
            conditions = []
            
            if filters.get("request_url"):
                conditions.append(SysLog.request_url.like(f"%{filters['request_url']}%"))
            
            if filters.get("request_method"):
                conditions.append(SysLog.request_method == filters['request_method'])
            
            if filters.get("visit_module"):
                conditions.append(SysLog.visit_module.like(f"%{filters['visit_module']}%"))
            
            if filters.get("operation_status"):
                conditions.append(SysLog.operation_status == filters['operation_status'])
            
            if filters.get("client_ip"):
                conditions.append(SysLog.client_ip == filters['client_ip'])
            
            if filters.get("start_time"):
                conditions.append(SysLog.request_time >= filters['start_time'])
            
            if filters.get("end_time"):
                conditions.append(SysLog.request_time <= filters['end_time'])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(SysLog.request_time.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total

    async def batch_delete(self, log_ids: List[int]) -> int:
        """
        批量删除日志
        
        Args:
            log_ids: 日志ID列表
            
        Returns:
            删除的记录数
        """
        query = delete(SysLog).where(SysLog.id.in_(log_ids))
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def delete_by_time_range(
        self, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None
    ) -> int:
        """
        按时间范围删除日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            删除的记录数
        """
        conditions = []
        
        if start_time:
            conditions.append(SysLog.request_time >= start_time)
        
        if end_time:
            conditions.append(SysLog.request_time <= end_time)
        
        if not conditions:
            return 0
        
        query = delete(SysLog).where(and_(*conditions))
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def delete_logs_before_days(self, days: int) -> int:
        """
        清空指定天数前的日志
        
        Args:
            days: 天数
            
        Returns:
            删除的记录数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        query = delete(SysLog).where(SysLog.request_time < cutoff_time)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def delete_all(self) -> int:
        """
        清空所有日志
        
        Returns:
            删除的记录数
        """
        query = delete(SysLog)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount
