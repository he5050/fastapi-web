from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import BaseResponse, PageData, PageResponse
from app.db.session import get_db
from app.schemas.base_schema import PaginationParams
from app.schemas.sys_log_schema import LogBatchDelete, LogCleanupByTime, SysLogOut
from app.services.sys_log_service import SysLogService

router = APIRouter(prefix="/sys-logs", tags=["日志管理"])


@router.get("/list", response_model=PageResponse[SysLogOut], summary="获取日志列表")
async def list_logs(
    pagination: PaginationParams = Depends(),
    requestUrl: Optional[str] = Query(None, description="请求URL筛选"),
    requestMethod: Optional[str] = Query(None, description="请求方法筛选"),
    visitModule: Optional[str] = Query(None, description="访问模块筛选"),
    operationStatus: Optional[str] = Query(None, description="操作状态筛选"),
    clientIp: Optional[str] = Query(None, description="客户端IP筛选"),
    startTime: Optional[str] = Query(None, description="开始时间(YYYY-MM-DD HH:mm:ss)"),
    endTime: Optional[str] = Query(None, description="结束时间(YYYY-MM-DD HH:mm:ss)"),
    db: AsyncSession = Depends(get_db),
) -> PageResponse[SysLogOut]:
    """
    获取日志列表，参数由 FastAPI 自动验证
    """
    service = SysLogService(db)

    # 构建过滤条件
    filters = {}
    if requestUrl:
        filters["request_url"] = requestUrl
    if requestMethod:
        filters["request_method"] = requestMethod
    if visitModule:
        filters["visit_module"] = visitModule
    if operationStatus:
        filters["operation_status"] = operationStatus
    if clientIp:
        filters["client_ip"] = clientIp
    if startTime:
        filters["start_time"] = startTime
    if endTime:
        filters["end_time"] = endTime

    data = await service.get_logs(pagination.page, pagination.page_size, **filters)
    page_data = PageData[SysLogOut](**data)
    return PageResponse(success=True, data=page_data, message="获取成功")


@router.delete("/batch", response_model=BaseResponse[int], summary="批量删除日志")
async def batch_delete_logs(
    obj_in: LogBatchDelete = Body(...), db: AsyncSession = Depends(get_db)
) -> BaseResponse[int]:
    """
    批量删除指定ID的日志记录
    """
    service = SysLogService(db)
    deleted_count = await service.batch_delete_logs(obj_in)
    return BaseResponse.success_res(
        data=deleted_count, message=f"成功删除{deleted_count}条日志"
    )


@router.post("/cleanup", response_model=BaseResponse[int], summary="清理日志")
async def cleanup_logs(
    obj_in: LogCleanupByTime = Body(...), db: AsyncSession = Depends(get_db)
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
