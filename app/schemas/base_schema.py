from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """
    基础 Schema，支持蛇形转驼峰命名转换
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


class PaginationParams(BaseSchema):
    """
    统一分页查询参数
    """

    page: int = 1
    page_size: int = 10
