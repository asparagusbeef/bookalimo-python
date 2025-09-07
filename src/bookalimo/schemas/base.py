"""
Shared base model for Book-A-Limo API data structures.
Handles automatic snake_case <-> camelCase conversion and enum serialization.
"""

from enum import Enum
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, model_serializer
from pydantic.alias_generators import to_camel
from pydantic_core.core_schema import SerializationInfo, SerializerFunctionWrapHandler


class ApiModel(BaseModel):
    """
    Base model for all Book-A-Limo API models.

    Provides automatic field name conversion between Python snake_case
    and API camelCase, plus proper enum handling.
    """

    model_config = ConfigDict(
        # Auto-generate camelCase aliases from snake_case field names
        alias_generator=to_camel,
        # Accept both alias (camel) and name (snake) on input (v2.11+)
        validate_by_alias=True,
        validate_by_name=True,  # replaces populate_by_name
        # Default to using aliases when dumping (wire format)
        serialize_by_alias=True,
        # Enums dumping handled in model_serializer
        use_enum_values=False,
        # Ignore unknown keys from the API
        extra="ignore",
    )

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        # Run the normal serialization first (aliases, include/exclude, nested models, etc.)
        data = handler(self)

        # Decide how to emit enums based on context (default to 'value')
        enum_out = (info.context or {}).get("enum_out", "value")

        def convert(obj: Any) -> Any:
            if isinstance(obj, Enum):
                return obj.name if enum_out == "name" else obj.value
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                t = type(obj)
                return t(convert(v) for v in obj)
            return obj

        return cast(dict[str, Any], convert(data))
