"""
Shared base model for Book-A-Limo API data structures.
Handles automatic snake_case <-> camelCase conversion and enum serialization.
"""

from enum import Enum
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, model_serializer
from pydantic.alias_generators import to_camel, to_snake
from pydantic_core.core_schema import SerializationInfo, SerializerFunctionWrapHandler


def _deep_to_snake(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            (to_snake(k) if isinstance(k, str) else k): _deep_to_snake(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_deep_to_snake(v) for v in obj]
    if isinstance(obj, tuple):
        return type(obj)(_deep_to_snake(v) for v in obj)
    return obj


class SharedModel(BaseModel):
    """
    Base model for shared data structures used in both API requests and responses.

    Provides field name conversion but no serialization opinions - subclasses decide
    whether to serialize to camelCase (for requests) or snake_case (for responses).
    """

    model_config = ConfigDict(
        # Auto-generate camelCase aliases from snake_case field names
        alias_generator=to_camel,
        # Accept both alias (camel) and name (snake) on input
        validate_by_alias=True,
        validate_by_name=True,
        # Don't set serialize_by_alias - let subclasses decide
        # Enums dumping handled in model_serializer
        use_enum_values=False,
        # Ignore unknown keys from the API
        extra="ignore",
    )


class RequestModel(SharedModel):
    """
    Base model for API request models.

    Serializes to camelCase by default (what the Book-A-Limo API expects).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,  # Serialize to camelCase for API requests
        use_enum_values=False,
        extra="ignore",
    )


class ResponseModel(SharedModel):
    """
    Base model for API response models.

    Serializes to snake_case by default (better DX for Python developers).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=False,  # Serialize to snake_case for Python developers
        use_enum_values=False,
        extra="ignore",
    )

    @model_serializer(mode="wrap")
    def _serialize(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        # Run the normal serialization first (aliases, include/exclude, nested models, etc.)
        data = handler(self)

        # Decide how to emit enums based on context (default to 'value')
        ctx = info.context or {}
        enum_out = ctx.get("enum_out", "value")

        def convert_values(obj: Any) -> Any:
            if isinstance(obj, Enum):
                return obj.name if enum_out == "name" else obj.value
            if isinstance(obj, dict):
                return {k: convert_values(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                t = type(obj)
                return t(convert_values(v) for v in obj)
            return obj

        out = cast(dict[str, Any], convert_values(data))

        # Key case control: default "camel" (uses aliases); allow "snake" via context.
        case = ctx.get("case")
        # Support boolean alias for convenience: snake_case=True -> case="snake"
        if ctx.get("snake_case") is True:
            case = "snake"
        elif ctx.get("snake_case") is False:
            case = "camel"

        if case == "snake":
            out = cast(dict[str, Any], _deep_to_snake(out))

        return out
