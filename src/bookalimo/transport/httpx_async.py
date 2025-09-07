"""Async HTTP transport using httpx."""

import logging
from time import perf_counter
from typing import Any, Optional, TypeVar, Union, overload
from uuid import uuid4

import httpx
from pydantic import BaseModel

from ..config import (
    DEFAULT_BACKOFF,
    DEFAULT_BASE_URL,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUTS,
    DEFAULT_USER_AGENT,
)
from ..exceptions import (
    BookalimoConnectionError,
    BookalimoError,
    BookalimoHTTPError,
    BookalimoRequestError,
    BookalimoTimeout,
)
from .auth import Credentials, inject_credentials
from .base import AsyncBaseTransport
from .retry import async_retry, should_retry_exception, should_retry_status
from .utils import handle_api_errors, handle_http_error

logger = logging.getLogger("bookalimo.transport")

T = TypeVar("T", bound=BaseModel)


class AsyncTransport(AsyncBaseTransport):
    """Async HTTP transport using httpx."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeouts: Any = DEFAULT_TIMEOUTS,
        user_agent: str = DEFAULT_USER_AGENT,
        credentials: Optional[Credentials] = None,
        client: Optional[httpx.AsyncClient] = None,
        retries: int = DEFAULT_RETRIES,
        backoff: float = DEFAULT_BACKOFF,
    ):
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials
        self.retries = retries
        self.backoff = backoff
        self.headers = {
            "content-type": "application/json",
            "user-agent": user_agent,
        }

        # Create client if not provided
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(timeout=timeouts)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "AsyncTransport initialized (base_url=%s, timeout=%s, user_agent=%s)",
                self.base_url,
                timeouts,
                user_agent,
            )

    @overload
    async def post(self, path: str, model: BaseModel) -> Any: ...
    @overload
    async def post(self, path: str, model: BaseModel, response_model: type[T]) -> T: ...

    async def post(
        self, path: str, model: BaseModel, response_model: Optional[type[T]] = None
    ) -> Union[T, Any]:
        """Make a POST request and return parsed response."""
        # Prepare URL
        path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{path}"

        # Prepare data and inject credentials
        data = self.prepare_data(model)
        data = inject_credentials(data, self.credentials)

        # Debug logging
        req_id = None
        start = 0.0
        if logger.isEnabledFor(logging.DEBUG):
            req_id = uuid4().hex[:8]
            start = perf_counter()
            body_keys = sorted(k for k in data.keys() if k != "credentials")
            logger.debug(
                "→ [%s] POST %s body_keys=%s",
                req_id,
                path,
                body_keys,
            )

        try:
            # Make request with retry logic
            response = await async_retry(
                lambda: self._make_request(url, data),
                retries=self.retries,
                backoff=self.backoff,
                should_retry=lambda e: should_retry_exception(e)
                or (
                    isinstance(e, httpx.HTTPStatusError)
                    and should_retry_status(e.response.status_code)
                ),
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                handle_http_error(response, req_id, path)

            # Parse JSON
            try:
                json_data = response.json()
            except ValueError as e:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.warning("× [%s] %s invalid JSON", req_id or "-", path)
                preview = (
                    (response.text or "")[:256] if hasattr(response, "text") else None
                )
                raise BookalimoError(
                    f"Invalid JSON response: {preview}",
                ) from e

            # Handle API-level errors
            handle_api_errors(json_data, req_id, path)

            # Debug logging for success
            if logger.isEnabledFor(logging.DEBUG):
                dur_ms = (perf_counter() - start) * 1000.0
                reqid_hdr = response.headers.get(
                    "x-request-id"
                ) or response.headers.get("request-id")
                content_len = (
                    len(response.content) if hasattr(response, "content") else None
                )
                logger.debug(
                    "← [%s] %s %s in %.1f ms len=%s reqid=%s",
                    req_id,
                    response.status_code,
                    path,
                    dur_ms,
                    content_len,
                    reqid_hdr,
                )

            # Parse and return response
            return (
                response_model.model_validate(json_data)
                if response_model
                else json_data
            )

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
                    "× [%s] %s request error: %s",
                    req_id or "-",
                    path,
                    e.__class__.__name__,
                )
            raise BookalimoRequestError(f"Request Error: {e}") from e

        except httpx.HTTPStatusError as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "× [%s] %s HTTP error: %s",
                    req_id or "-",
                    path,
                    e.__class__.__name__,
                )
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            raise BookalimoHTTPError(f"HTTP Error: {e}", status_code=status_code) from e

        except (BookalimoError, BookalimoHTTPError):
            # Already handled above
            raise

        except Exception as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(
                    "× [%s] %s unexpected error: %s",
                    req_id or "-",
                    path,
                    e.__class__.__name__,
                )
            raise BookalimoError(f"Unexpected error: {str(e)}") from e

    async def _make_request(self, url: str, data: dict[str, Any]) -> httpx.Response:
        """Make the actual HTTP request."""
        resp = await self.client.post(url, json=data, headers=self.headers)
        if should_retry_status(resp.status_code):
            # Construct an HTTPStatusError so async_retry can catch & decide.
            raise httpx.HTTPStatusError(
                message=f"Retryable HTTP status: {resp.status_code}",
                request=resp.request,
                response=resp,
            )
        return resp

    async def aclose(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client and not self.client.is_closed:
            await self.client.aclose()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("AsyncTransport HTTP client closed")

    async def __aenter__(self) -> "AsyncTransport":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.aclose()
