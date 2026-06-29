from decimal import Decimal

from pydantic import BaseModel as PydanticBaseModel
from pydantic import field_serializer


class BaseModel(PydanticBaseModel):
    """DTO基类：自动将Decimal字段序列化为float，避免前端收到字符串数值"""

    @field_serializer("*", when_used="json")
    def _serialize_decimal_fields(self, v, _info):
        if isinstance(v, Decimal):
            return float(v)
        return v
