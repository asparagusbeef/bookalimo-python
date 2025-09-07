from __future__ import annotations

import inspect
from functools import lru_cache
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
    get_args,
    get_origin,
)

from google.protobuf import json_format as jf

# Protobuf imports
from google.protobuf.message import Message as GPBMessage
from pydantic import BaseModel, TypeAdapter
from pydantic_core import ValidationError

# Logging
from ...logging import get_logger

TModel = TypeVar("TModel", bound=BaseModel)

log = get_logger("proto_adapter")

# ---------------- Proto extraction (proto-plus or vanilla GPB) ----------------


def _extract_gpb_message(msg: Any) -> GPBMessage:
    if isinstance(msg, GPBMessage):
        return msg
    for attr in ("_pb", "pb"):
        if hasattr(msg, attr):
            cand = getattr(msg, attr)
            if isinstance(cand, GPBMessage):
                return cand
    for meth in ("to_protobuf", "to_pb"):
        if hasattr(msg, meth):
            cand = getattr(msg, meth)()
            if isinstance(cand, GPBMessage):
                return cand
    raise TypeError(
        "Unsupported protobuf message type. Provide a google.protobuf Message "
        "or a proto-plus message exposing ._pb/.pb or .to_protobuf()."
    )


# ---------------- Version-proof MessageToDict wrapper ----------------


@lru_cache(maxsize=1)
def _mtodict_signature() -> inspect.Signature:
    return inspect.signature(jf.MessageToDict)


def _message_to_dict(
    msg: Any,
    *,
    use_integers_for_enums: bool = True,
    including_default_value_fields: bool = False,
    preserving_proto_field_name: bool = True,
) -> dict[str, Any]:
    """
    Wraps google.protobuf.json_format.MessageToDict with runtime arg mapping
    so it works across protobuf versions.
    """
    gpb = _extract_gpb_message(msg)
    sig = _mtodict_signature()
    params = sig.parameters

    kwargs: dict[str, Any] = {
        "preserving_proto_field_name": preserving_proto_field_name,
        "use_integers_for_enums": use_integers_for_enums,
    }

    # protobuf>=5 uses "always_print_fields_with_no_presence"
    if "including_default_value_fields" in params:
        kwargs["including_default_value_fields"] = including_default_value_fields
    elif "always_print_fields_with_no_presence" in params:
        # Map our public arg to the new name
        kwargs["always_print_fields_with_no_presence"] = including_default_value_fields
    # else: neither supported (very old?) -> omit, default behavior

    try:
        return jf.MessageToDict(gpb, **kwargs)
    except Exception as e:
        log.error(f"MessageToDict conversion failed: {e}")
        raise


# ---------------- Optional base64 -> bytes coercion guided by model schema ----------------


def _unwrap_optional(tp: Any) -> Any:
    if get_origin(tp) is Optional:
        return get_args(tp)[0]
    return tp


def _coerce_by_annotation(data: Any, annotation: Any) -> Any:
    from base64 import urlsafe_b64decode

    from pydantic import BaseModel as PydBaseModel

    if annotation is None:
        return data

    if get_origin(annotation) is Optional:
        annotation = _unwrap_optional(annotation)

    if annotation is bytes and isinstance(data, str):
        # tolerate missing padding
        try:
            return urlsafe_b64decode(data + "===")
        except Exception:
            return data

    if get_origin(annotation) in (list, tuple, List, Tuple):
        (item_type,) = get_args(annotation) or (Any,)
        if isinstance(data, list):
            return [_coerce_by_annotation(x, item_type) for x in data]
        return data

    if get_origin(annotation) in (dict, Dict):
        args = get_args(annotation)
        if len(args) == 2 and isinstance(data, dict):
            _, v_type = args
            return {k: _coerce_by_annotation(v, v_type) for k, v in data.items()}
        return data

    if (
        isinstance(annotation, type)
        and issubclass(annotation, PydBaseModel)
        and isinstance(data, dict)
    ):
        out = dict(data)
        for fname, f in annotation.model_fields.items():
            keys = [fname]
            if f.alias and f.alias != fname:
                keys.insert(0, f.alias)
            present = next((k for k in keys if k in out), None)
            if present is not None:
                out[present] = _coerce_by_annotation(out[present], f.annotation)
        return out

    return data


# ---------------- TypeAdapter cache (generic-erased to appease Pyright) ----------------


@lru_cache(maxsize=256)
def _adapter_for_cached(model_cls: type) -> TypeAdapter[BaseModel]:
    # erase generic in the cache to avoid TypeVar identity issues in type checkers
    return TypeAdapter(model_cls)


# ---------------- Public API ----------------


def validate_proto_to_model(
    msg: Any,
    model_type: Type[TModel],
    *,
    decode_bytes_by_schema: bool = True,
    use_integers_for_enums: bool = True,
    including_default_value_fields: bool = False,
    preserving_proto_field_name: bool = True,
) -> TModel:
    """
    Validate a protobuf message (proto-plus or GPB) into a Pydantic v2 model instance.

    - Works across protobuf versions (handles arg rename to always_print_fields_with_no_presence).
    - Fully runtime: you pass the concrete Pydantic model class.
    """
    # Convert protobuf to dictionary
    try:
        raw = _message_to_dict(
            msg,
            use_integers_for_enums=use_integers_for_enums,
            including_default_value_fields=including_default_value_fields,
            preserving_proto_field_name=preserving_proto_field_name,
        )
    except Exception as e:
        log.error(f"Failed to convert protobuf to dict: {e}")
        raise

    # Apply type coercion if enabled
    try:
        data = _coerce_by_annotation(raw, model_type) if decode_bytes_by_schema else raw
    except Exception as e:
        log.error(f"Failed during type coercion: {e}")
        raise

    # Validate with Pydantic
    try:
        adapter = _adapter_for_cached(model_type)
        result = cast(TModel, adapter.validate_python(data))
        return result

    except ValidationError as e:
        log.error(
            f"Pydantic validation failed for {model_type.__name__} ({e.error_count()} errors)"
        )

        # Log key validation errors with context
        for error in e.errors():
            if "loc" in error and error["loc"]:
                location = ".".join(str(loc) for loc in error["loc"])
                log.error(f"Validation error at {location}: {error['msg']}")
            else:
                log.error(f"Validation error: {error['msg']}")

        raise

    except Exception as e:
        log.error(f"Unexpected error during validation: {e}")
        raise
