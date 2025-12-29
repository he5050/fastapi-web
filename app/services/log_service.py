from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.repositories.log_repository import SysLogRepository
from app.schemas.log_schema import LogBatchDelete, LogCleanupByTime


class SysLogService:
    """
    系统日志业务逻辑层
    """

    def __init__(self, db: AsyncSession):
        self.repo = SysLogRepository(db)

    async def get_logs(self, page: int, page_size: int, **filters) -> Dict[str, Any]:
        """
        获取日志列表

        Args:
            page: 页码
            page_size: 每页数量
            **filters: 过滤条件

        Returns:
            分页数据
        """
        # 参数校验
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        # 构建过滤条件
        filter_dict = {}

        if filters.get("request_url"):
            filter_dict["request_url"] = filters["request_url"]

        if filters.get("request_method"):
            filter_dict["request_method"] = filters["request_method"]

        if filters.get("visit_module"):
            filter_dict["visit_module"] = filters["visit_module"]

        if filters.get("operation_status"):
            filter_dict["operation_status"] = filters["operation_status"]

        if filters.get("client_ip"):
            filter_dict["client_ip"] = filters["client_ip"]

        if filters.get("start_time"):
            try:
                start_time = datetime.fromisoformat(filters["start_time"])
                filter_dict["start_time"] = start_time
            except (ValueError, TypeError):
                raise AppError("开始时间格式错误")

        if filters.get("end_time"):
            try:
                end_time = datetime.fromisoformat(filters["end_time"])
                filter_dict["end_time"] = end_time
            except (ValueError, TypeError):
                raise AppError("结束时间格式错误")

        # 时间范围校验
        if filter_dict.get("start_time") and filter_dict.get("end_time"):
            if filter_dict["start_time"] > filter_dict["end_time"]:
                raise AppError("开始时间不能晚于结束时间")

        items, total = await self.repo.get_list(page, page_size, filter_dict)
        total_page = (total + page_size - 1) // page_size

        return {
            "records": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_page": total_page,
        }

    async def batch_delete_logs(self, obj_in: LogBatchDelete) -> int:
        """
        批量删除日志

        Args:
            obj_in: 批量删除请求对象

        Returns:
            删除的记录数
        """
        if not obj_in.log_ids:
            raise AppError("日志ID列表不能为空")

        if len(obj_in.log_ids) > 1000:
            raise AppError("单次删除日志数量不能超过1000条")

        deleted_count = await self.repo.batch_delete(obj_in.log_ids)

        if deleted_count == 0:
            raise AppError("未找到要删除的日志记录")

        return deleted_count

    async def cleanup_logs(self, obj_in: LogCleanupByTime) -> int:
        """
        清理日志

        Args:
            obj_in: 清理请求对象

        Returns:
            删除的记录数
        """
        # 时间范围校验
        if obj_in.start_time > obj_in.end_time:
            raise AppError("开始时间不能晚于结束时间")

        deleted_count = await self.repo.delete_by_time_range(
            start_time=obj_in.start_time, end_time=obj_in.end_time
        )

        if deleted_count == 0:
            raise AppError("未找到符合清理条件的日志记录")

        return deleted_count

    async def clear_all_logs(self) -> int:
        """
        清空所有日志

        Returns:
            删除的记录数
        """
        deleted_count = await self.repo.delete_all()
        return deleted_count
