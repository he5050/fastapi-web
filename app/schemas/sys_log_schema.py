from typing import Optional, List
from pydantic import Field
from datetime import datetime
from app.schemas.base_schema import BaseSchema


class SysLogOut(BaseSchema):
    """
    系统日志输出 Schema
    """

    id: int = Field(..., description="日志ID")
    request_url: str = Field(..., description="请求接口URL")
    request_method: str = Field(..., description="请求方法")
    request_params: Optional[str] = Field(None, description="请求参数(JSON格式)")
    visit_module: Optional[str] = Field(None, description="访问模块")
    operation_type: Optional[str] = Field(None, description="操作类型")
    operation_status: str = Field(..., description="操作结果(success/failure)")
    response_result: Optional[str] = Field(None, description="返回结果(JSON格式)")
    request_time: datetime = Field(..., description="请求时间")
    duration: Optional[int] = Field(None, description="耗时(毫秒)")
    user_info: Optional[str] = Field(None, description="用户信息(JSON格式)")
    client_ip: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="客户端User-Agent")
    created_at: datetime = Field(..., description="创建时间")


class LogBatchDelete(BaseSchema):
    """
    批量删除日志请求 Schema
    """

    log_ids: List[int] = Field(..., description="日志ID列表", min_length=1)


class LogCleanupByTime(BaseSchema):
    """
    按时间清理日志请求 Schema
    """

    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    days: Optional[int] = Field(7, description="清理多少天前的日志，默认7天", ge=1)
