from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """
    基础 Schema，支持蛇形转驼峰
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )
