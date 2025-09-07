import logging
from typing import Any, Optional

import httpx

from ..exceptions import BookalimoError, BookalimoHTTPError, BookalimoTimeout

logger = logging.getLogger("bookalimo.transport")


def handle_api_errors(
    json_data: Any,
    req_id: Optional[str],
    path: str,
) -> None:
    """Handle API-level errors in the response."""
    if not isinstance(json_data, dict):
        return

    if json_data.get("error"):
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning("× [%s] %s API error", req_id or "-", path)
        raise BookalimoError(f"API Error: {json_data['error']}")

    if "success" in json_data and not json_data["success"]:
        msg = json_data.get("error", "Unknown API error")
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning("× [%s] %s API error", req_id or "-", path)
        raise BookalimoError(f"API Error: {msg}")


def handle_http_error(
    response: httpx.Response, req_id: Optional[str], path: str
) -> None:
    """Handle HTTP status errors."""
    status = response.status_code

    if status == 408:
        raise BookalimoTimeout(f"HTTP {status}: Request timeout")
    elif status in (502, 503, 504):
        raise BookalimoHTTPError(
            f"HTTP {status}: Service unavailable", status_code=status
        )

    # Try to parse error payload
    try:
        payload = response.json()
    except Exception as e:
        text_preview = (response.text or "")[:256] if hasattr(response, "text") else ""
        raise BookalimoHTTPError(
            f"HTTP {status}: {text_preview}",
            status_code=status,
        ) from e

    raise BookalimoHTTPError(
        f"HTTP {status}",
        status_code=status,
        payload=payload if isinstance(payload, dict) else {"raw": payload},
    )
