from datetime import datetime
from typing import List, Optional, Any

from pydantic import Field, field_validator

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

    start_time: datetime = Field(
        ..., description="开始时间，格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DDTHH:MM:SS"
    )
    end_time: datetime = Field(
        ..., description="结束时间，格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DDTHH:MM:SS"
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        """
        解析多种日期时间格式
        支持格式：
        - 2025-12-29 21:45:06 (空格分隔)
        - 2025-12-29T21:45:06 (ISO 8601，带 T)
        - 2025-12-29 21:45:06.123 (带毫秒)
        - 2025-12-29T21:45:06.123 (ISO 8601，带 T 和毫秒)
        """
        if isinstance(v, datetime):
            return v

        if v is None:
            raise ValueError("时间不能为空")

        if not isinstance(v, str):
            raise ValueError("时间格式必须是字符串")

        # 尝试多种格式
        formats = [
            "%Y-%m-%d %H:%M:%S",  # 2025-12-29 21:45:06
            "%Y-%m-%dT%H:%M:%S",  # 2025-12-29T21:45:06
            "%Y-%m-%d %H:%M:%S.%f",  # 2025-12-29 21:45:06.123
            "%Y-%m-%dT%H:%M:%S.%f",  # 2025-12-29T21:45:06.123
        ]

        for fmt in formats:
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue

        # 如果所有格式都失败，尝试 Pydantic 的默认解析
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(
                f"时间格式错误，支持格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DDTHH:MM:SS，实际值：{v}"
            )