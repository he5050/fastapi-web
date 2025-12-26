from typing import Any
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """
    基础 Schema，支持蛇形转驼峰及统一时间格式
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    @field_serializer("*")
    def serialize_datetime(self, value: Any) -> Any:
        # 优先判断 datetime（因为它包含信息最全）
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        # 再判断 date (仅年月日)
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")

        return value
