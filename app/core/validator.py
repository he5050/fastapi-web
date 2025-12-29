import re
from typing import Any, Callable, List, Optional, Union


class ValidationRule:
    """
    Antd 风格的校验规则定义
    """

    def __init__(
        self,
        required: Optional[bool] = None,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        pattern: Optional[str] = None,
        message: str = "校验失败",
        validator: Optional[Callable[[Any], bool]] = None,
    ):
        self.required = required
        self.min_len = min_len
        self.max_len = max_len
        self.pattern = pattern
        self.message = message
        self.validator = validator


def validate_rules(value: Any, rules: List[ValidationRule]) -> Any:
    """
    执行规则校验逻辑
    """
    for rule in rules:
        # 1. 必填校验
        if rule.required:
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(rule.message)

        # 如果值为 None 且不是必填，则跳过后续校验
        if value is None:
            continue

        # 2. 最小长度/值校验
        if rule.min_len is not None:
            if isinstance(value, (str, list, tuple)) and len(value) < rule.min_len:
                raise ValueError(rule.message)
            if isinstance(value, (int, float)) and value < rule.min_len:
                raise ValueError(rule.message)

        # 3. 最大长度/值校验
        if rule.max_len is not None:
            if isinstance(value, (str, list, tuple)) and len(value) > rule.max_len:
                raise ValueError(rule.message)
            if isinstance(value, (int, float)) and value > rule.max_len:
                raise ValueError(rule.message)

        # 4. 正则校验
        if rule.pattern is not None:
            if not re.match(rule.pattern, str(value)):
                raise ValueError(rule.message)

        # 5. 自定义校验函数
        if rule.validator is not None:
            if not rule.validator(value):
                raise ValueError(rule.message)

    return value
