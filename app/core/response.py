from typing import Any, Optional, Generic, TypeVar
from app.schemas.base_schema import BaseSchema

T = TypeVar("T")


class BaseResponse(BaseSchema, Generic[T]):
    """
    统一响应格式
    """

    success: bool = True
    data: Optional[T] = None
    message: str = ""

    @classmethod
    def success_res(cls, data: Any = None, message: str = "成功") -> "BaseResponse":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail_res(cls, message: str = "失败", data: Any = None) -> "BaseResponse":
        return cls(success=False, data=data, message=message)


class PageData(BaseSchema, Generic[T]):
    """
    分页数据容器
    """

    records: list[T]
    total: int
    page: int
    page_size: int
    total_page: int


class PageResponse(BaseResponse[PageData[T]], Generic[T]):
    """
    统一分页响应格式
    """

    pass
