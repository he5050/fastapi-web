from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """
    基础 Schema，支持蛇形转驼峰及统一时间格式
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    @model_serializer(mode='wrap', when_used='json')
    def _serialize_model(self, serializer: Any) -> dict[str, Any]:
        """
        自定义模型序列化器，处理datetime和date类型的统一格式化
        使用wrap模式包装默认序列化器，避免field_serializer("*")的兼容性问题
        """
        # 先调用默认序列化器获取字典
        data = serializer(self)

        # 遍历所有字段，格式化datetime和date类型
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, date):
                    data[key] = value.strftime("%Y-%m-%d")

        return data


class PaginationParams(BaseSchema):
    """
    统一分页查询参数
    """

    page: int = 1
    page_size: int = 10
