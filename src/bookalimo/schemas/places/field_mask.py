from __future__ import annotations

import warnings
from typing import (
    Any,
    Callable,
    Iterable,
    NewType,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel

from .common import ExternalModel
from .place import GooglePlace

FieldMaskInput = Union[str, "FieldPath", Iterable[Union[str, "FieldPath"]]]
FieldTreeType = NewType("FieldTreeType", dict[str, Any])

# Sentinel meaning “anything under this node is allowed”
ANY = object()


def _unwrap(t: Any) -> Any:
    """Unwrap Optional[T], list[T], etc. Return (base_type, is_list)."""
    origin = get_origin(t)
    args = get_args(t)
    # Optional[T] is Union[T, NoneType]
    if origin is Union and args:
        non_none = [a for a in args if a is not type(None)]  # noqa: E721
        if len(non_none) == 1:
            return _unwrap(non_none[0])
    if origin in (list, tuple, set):
        inner = args[0] if args else Any
        base, _ = _unwrap(inner)
        return base, True
    return t, False


def _is_model(t: Any) -> bool:
    try:
        return issubclass(t, BaseModel)
    except Exception:
        return False


def _is_external_model(t: Any) -> bool:
    try:
        return issubclass(t, ExternalModel)
    except Exception:
        return False


def build_field_tree(root: Type[BaseModel]) -> FieldTreeType:
    return _build_field_tree(root)


def _build_field_tree(root: Type[BaseModel]) -> FieldTreeType:
    """
    Introspect a Pydantic v2 model into a nested dict:
      { field_name: dict(...) | ANY | None }
    - dict(...)  => we know nested fields (another BaseModel with declared fields)
    - ANY        => ExternalModel (extra=allow) or otherwise permissive; allow any nested
    - None       => leaf / scalar
    """
    tree = {}

    # v2: model_fields holds FieldInfo by name
    for name, fi in root.model_fields.items():
        t, is_list = _unwrap(fi.annotation)
        if _is_model(t):
            if _is_external_model(t):
                tree[name] = ANY
            else:
                # recurse into structured models
                tree[name] = _build_field_tree(t)
        else:
            # Non-model (scalar or collection of scalars)
            tree[name] = None
    return FieldTreeType(tree)


# Cache once
_FIELD_TREE = build_field_tree(GooglePlace)


def _validate_path(path: str, tree: FieldTreeType) -> Optional[tuple[str, str, str]]:
    """
    Validate a dotted path against the field tree.
    Returns None if OK, else a human-friendly warning string.
    """
    parts = path.split(".")
    node: Any = tree
    for i, seg in enumerate(parts):
        if not isinstance(node, dict):
            warn = f"'{'.'.join(parts[:i])}' is not an object, cannot select '{seg}'"
            return warn, path, seg
        if seg not in node:
            warn = f"Unknown field '{seg}' at '{'.'.join(parts[:i]) or '<root>'}'"
            return warn, path, seg
        node = node[seg]
        if node is ANY:
            # Wildcard subtree: allow anything under it
            return None
    return None  # fully validated


def compile_field_mask(
    fields: FieldMaskInput,
    *,
    prefix: str = "",
    on_warning: Optional[Callable[[str, str, str], None]] = None,
    allow_star: bool = True,
    extra_allowed_fields: Optional[list[str]] = None,
    field_tree: Optional[FieldTreeType] = _FIELD_TREE,
) -> list[str]:
    """
    Normalize + validate a field mask against a Pydantic model.
    (mirroring the Google Places API `Place` model).
    - Accepts: iterable of strings or FieldPath objects, or a single string (comma-separated ok).
    - Dedupes, preserves order.
    - Prefixes each with 'prefix' unless it already starts with that.
    - Emits warnings via on_warning(...) but never raises on unknown nested under ExternalModel.

    Args:
        fields: FieldMaskInput
        prefix: Prefix to add to each field
        on_warning: Optional callable on_warning(warn, path, seg) -> None. If not provided, uses the default warning handler.
        allow_star: Whether to allow the star wildcard
        extra_allowed_fields: Optional list of fields to allow even if they are not in the field tree.
        field_tree: Optional field tree to use instead of the default one.
    Usage:
    >>> compile_field_mask(F.display_name)
    ["display_name"]
    >>> compile_field_mask(["reviews.text", "reviews.author_name"])
    ["reviews.text"]
    >>> compile_field_mask("photos.author_attributions,photos.author_attributions.text")
    ["photos.author_attributions", "photos.author_attributions.text"]
    """
    if extra_allowed_fields is None:
        extra_allowed_fields = []
    # Flatten to a list of strings
    if isinstance(fields, str):
        items: Iterable[str] = sum((s.split(",") for s in fields.split()), [])
        items = [s.strip() for s in items if s.strip()]
    elif isinstance(fields, FieldPath):
        items = [str(fields)]
    else:
        items = [str(x).strip() for x in fields if str(x).strip()]

    if not items:
        return ["*"] if allow_star else []

    seen = set()
    ordered: list[str] = []
    for raw in items:
        if raw == "*":
            # Keep '*' as-is, but usually only as the sole field
            if allow_star and "*" not in seen:
                seen.add("*")
                ordered = ["*"]  # star trumps everything else
            continue

        path = raw  # snake_case already; don't transform
        not_valid = None
        if path not in extra_allowed_fields:
            not_valid = _validate_path(path, field_tree or _FIELD_TREE)
        if not_valid:
            warn, path, seg = not_valid
            if on_warning:
                on_warning(warn, path, seg)
            else:
                warnings.warn(warn, UserWarning, stacklevel=2)

        if prefix and not path.startswith(prefix):
            path = f"{prefix}.{path}"

        if path not in seen:
            seen.add(path)
            ordered.append(path)

    # If '*' was included alongside others, Google prefers just '*'
    if "*" in seen:
        return ["*"]

    return ordered


# ---- Tiny ergonomic builder for dotted paths ----
class FieldPath:
    __slots__ = ("path",)

    def __init__(self, path: str):
        self.path = path

    def __getattr__(self, name: str) -> FieldPath:
        return FieldPath(f"{self.path}.{name}")

    def __str__(self) -> str:
        return self.path


class _Root:
    def __getattr__(self, name: str) -> FieldPath:
        return FieldPath(name)


F = _Root()  # Usage: F.display_name, F.reviews.text, F.photos.author_attributions


if __name__ == "__main__":
    print(
        compile_field_mask(
            "photos.author_attributions,photos.author_attributions.textt",
            prefix="places",
        )
    )
