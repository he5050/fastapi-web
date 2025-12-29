from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import BaseResponse, PageData, PageResponse
from app.db.session import get_db
from app.schemas.sys_log_schema import LogBatchDelete, LogCleanupByTime, SysLogOut
from app.services.sys_log_service import SysLogService

router = APIRouter(prefix="/sys-logs", tags=["日志管理"])


@router.get("/list", response_model=PageResponse[SysLogOut], summary="获取日志列表")
async def list_logs(
    page: int = Query(1, ge=1, le=10000, description="页码"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize", description="每页数量"),
    request_url: Optional[str] = Query(None, description="请求URL筛选"),
    request_method: Optional[str] = Query(None, description="请求方法筛选"),
    visit_module: Optional[str] = Query(None, description="访问模块筛选"),
    operation_status: Optional[str] = Query(None, description="操作状态筛选"),
    client_ip: Optional[str] = Query(None, description="客户端IP筛选"),
    start_time: Optional[str] = Query(None, description="开始时间(ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间(ISO格式)"),
    db: AsyncSession = Depends(get_db),
) -> PageResponse[SysLogOut]:
    """
    获取日志列表，参数由 FastAPI 自动验证
    """
    service = SysLogService(db)

    # 构建过滤条件
    filters = {}
    if request_url:
        filters["request_url"] = request_url
    if request_method:
        filters["request_method"] = request_method
    if visit_module:
        filters["visit_module"] = visit_module
    if operation_status:
        filters["operation_status"] = operation_status
    if client_ip:
        filters["client_ip"] = client_ip
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time

    data = await service.get_logs(page, page_size, **filters)
    page_data = PageData[SysLogOut](**data)
    return PageResponse(success=True, data=page_data, message="获取成功")


@router.delete("/batch", response_model=BaseResponse[int], summary="批量删除日志")
async def batch_delete_logs(
    obj_in: LogBatchDelete, db: AsyncSession = Depends(get_db)
) -> BaseResponse[int]:
    """
    批量删除指定ID的日志记录
    """
    service = SysLogService(db)
    deleted_count = await service.batch_delete_logs(obj_in)
    return BaseResponse.success_res(
        data=deleted_count, message=f"成功删除{deleted_count}条日志"
    )


@router.delete("/cleanup", response_model=BaseResponse[int], summary="清理日志")
async def cleanup_logs(
    obj_in: LogCleanupByTime, db: AsyncSession = Depends(get_db)
) -> BaseResponse[int]:
    """
    清理指定时间范围内的日志
    """
    print(obj_in)
    service = SysLogService(db)
    deleted_count = await service.cleanup_logs(obj_in)
    return BaseResponse.success_res(
        data=deleted_count, message=f"成功清理{deleted_count}条日志"
    )


@router.delete("/clear-all", response_model=BaseResponse[int], summary="清空所有日志")
async def clear_all_logs(db: AsyncSession = Depends(get_db)) -> BaseResponse[int]:
    """
    清空所有日志记录（请谨慎使用）
    """
    service = SysLogService(db)
    deleted_count = await service.clear_all_logs()
    return BaseResponse.success_res(
        data=deleted_count, message=f"成功清空所有{deleted_count}条日志"
    )
