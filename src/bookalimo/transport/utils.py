import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Any, Callable, Generator, NoReturn, Optional, Union, cast, overload

import httpx

from ..exceptions import (
    BookalimoConnectionError,
    BookalimoError,
    BookalimoHTTPError,
    BookalimoRequestError,
    BookalimoTimeout,
)
from ..logging import configure_httpx_logging, redact_url

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
) -> NoReturn:
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


def build_url(base_url: str, path: str) -> str:
    """Build full URL ensuring a single leading slash on path and no trailing slash on base."""
    norm_base = base_url.rstrip("/")
    norm_path = path if path.startswith("/") else f"/{path}"
    return f"{norm_base}{norm_path}"


def get_request_id(resp: httpx.Response) -> Optional[str]:
    """Extract a request id header if present."""
    return cast(Optional[str], resp.headers.get("x-request-id")) or cast(
        Optional[str], resp.headers.get("request-id")
    )


def parse_json_or_raise(
    response: httpx.Response, path: str, req_id: Optional[str]
) -> Any:
    """Parse response JSON or raise a helpful error with preview.

    Returns parsed JSON value on success; raises BookalimoError on invalid JSON.
    """
    try:
        return response.json()
    except ValueError as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning("× [%s] %s invalid JSON", req_id or "-", path)
        preview = (response.text or "")[:256] if hasattr(response, "text") else ""
        raise BookalimoError(f"Invalid JSON response: {preview}") from e


def raise_if_retryable_status(
    response: httpx.Response, should_retry_status: Callable[[int], bool]
) -> None:
    """Raise httpx.HTTPStatusError for retryable status codes so retry logic can handle it."""
    if should_retry_status(response.status_code):
        raise httpx.HTTPStatusError(
            message=f"Retryable HTTP status: {response.status_code}",
            request=response.request,
            response=response,
        )


def pre_log(url: str, body_keys: list[str], req_id: str) -> None:
    """Standard pre-request debug log."""
    logger.debug("→ [%s] POST %s body_keys=%s", req_id, redact_url(url), body_keys)


def post_log(url: str, response: httpx.Response, start: float, req_id: str) -> None:
    """Standard post-response debug log."""
    dur_ms = (perf_counter() - start) * 1000.0
    content_len = len(response.content) if hasattr(response, "content") else None
    logger.debug(
        "← [%s] %s %s in %.1f ms len=%s reqid=%s",
        req_id,
        response.status_code,
        redact_url(url),
        dur_ms,
        content_len,
        get_request_id(response),
    )


@contextmanager
def map_httpx_exceptions(
    req_id: Optional[str], path: str
) -> Generator[None, None, None]:
    """Map common httpx exceptions to domain-specific exceptions.

    Ensures we consistently translate low-level httpx errors.
    """
    try:
        yield
    except httpx.TimeoutException:
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning("× [%s] %s timeout", req_id or "-", path)
        raise BookalimoTimeout("Request timeout") from None
    except httpx.ConnectError:
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning("× [%s] %s connection error", req_id or "-", path)
        raise BookalimoConnectionError(
            "Connection error - unable to reach Book-A-Limo API"
        ) from None
    except httpx.RequestError as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning(
                "× [%s] %s request error: %s", req_id or "-", path, e.__class__.__name__
            )
        # Preserve underlying message
        raise BookalimoRequestError(f"Request Error: {e}") from e
    except httpx.HTTPStatusError as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.warning(
                "× [%s] %s HTTP error: %s", req_id or "-", path, e.__class__.__name__
            )
        status_code = getattr(getattr(e, "response", None), "status_code", None)
        raise BookalimoHTTPError(f"HTTP Error: {e}", status_code=status_code) from e


def log_request(request: httpx.Request) -> None:
    """Event hook to log HTTP requests with redacted URLs (sync version)."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "HTTP Request: %s %s",
            request.method,
            redact_url(str(request.url)),
        )


async def log_request_async(request: httpx.Request) -> None:
    """Event hook to log HTTP requests with redacted URLs (async version)."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "HTTP Request: %s %s",
            request.method,
            redact_url(str(request.url)),
        )


def _log_response(response: httpx.Response) -> None:
    """Event hook to log HTTP responses with redacted URLs."""
    if logger.isEnabledFor(logging.DEBUG):
        request = response.request
        logger.debug(
            "HTTP Response: %s %s -> %d",
            request.method,
            redact_url(str(request.url)),
            response.status_code,
        )


def log_response(response: httpx.Response) -> None:
    """Event hook to log HTTP responses with redacted URLs."""
    _log_response(response)


async def log_response_async(response: httpx.Response) -> None:
    """Event hook to log HTTP responses with redacted URLs."""
    _log_response(response)


@overload
def setup_secure_logging_and_client(
    *,
    is_async: bool,
    timeout: Any,
    client: Optional[httpx.AsyncClient],
) -> tuple[httpx.AsyncClient, bool]: ...


@overload
def setup_secure_logging_and_client(
    *,
    is_async: bool,
    timeout: Any,
    client: Optional[httpx.Client],
) -> tuple[httpx.Client, bool]: ...


def setup_secure_logging_and_client(
    *,
    is_async: bool,
    timeout: Any,
    client: Optional[Union[httpx.Client, httpx.AsyncClient]] = None,
) -> tuple[Union[httpx.Client, httpx.AsyncClient], bool]:
    """
    Configure secure logging and create httpx client with event hooks if needed.

    Returns:
        Tuple of (client, owns_client_flag)
    """
    # Configure httpx logging to prevent sensitive data exposure
    configure_httpx_logging()

    if client is not None:
        return client, False

    # Create client with secure logging event hooks
    event_hooks: dict[str, list[Callable[..., Any]]] = (
        {
            "request": [log_request_async if is_async else log_request],
            "response": [log_response_async if is_async else log_response],
        }
        if logger.isEnabledFor(logging.DEBUG)
        else {}
    )

    if is_async:
        return httpx.AsyncClient(timeout=timeout, event_hooks=event_hooks), True
    else:
        return httpx.Client(timeout=timeout, event_hooks=event_hooks), True
