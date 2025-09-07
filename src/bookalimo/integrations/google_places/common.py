"""
Common utilities and shared functionality for Google Places clients.
"""

from __future__ import annotations

from collections.abc import Sequence

from ...logging import get_logger

logger = get_logger("places")


def fmt_exc(e: BaseException) -> str:
    """Format exception for logging without touching non-existent attributes."""
    return f"{type(e).__name__}: {e}"


def mask_header(fields: Sequence[str] | str | None) -> tuple[tuple[str, str], ...]:
    """
    Build the X-Goog-FieldMask header. Pass a comma-separated string or a sequence.
    If None, no header is added (e.g., autocomplete, get_photo_media).
    """
    if fields is None:
        return ()
    if isinstance(fields, str):
        value = fields
    else:
        value = ",".join(fields)
    return (("X-Goog-FieldMask", value),)


# Default field mask for places queries
DEFAULT_PLACE_FIELDS = (
    "id",
    "displayName",
    "formattedAddress",
    "location",
)
