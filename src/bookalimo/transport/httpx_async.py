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
from ..logging import redact_url
from .auth import Credentials, inject_credentials
from .base import AsyncBaseTransport
from .retry import async_retry, should_retry_exception, should_retry_status
from .utils import (
    build_url,
    handle_api_errors,
    handle_http_error,
    map_httpx_exceptions,
    parse_json_or_raise,
    post_log,
    pre_log,
    raise_if_retryable_status,
    setup_secure_logging_and_client,
)

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
        self._credentials = credentials
        self.retries = retries
        self.backoff = backoff
        self.headers = {
            "content-type": "application/json",
            "user-agent": user_agent,
        }

        # Setup secure logging and create client
        self.client, self._owns_client = setup_secure_logging_and_client(
            is_async=True, timeout=timeouts, client=client
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "%s initialized (base_url=%s, timeout=%s, user_agent=%s)",
                self.__class__.__name__,
                redact_url(self.base_url),
                timeouts,
                user_agent,
            )

    @property
    def credentials(self) -> Optional[Credentials]:
        return self._credentials

    @credentials.setter
    def credentials(self, credentials: Optional[Credentials]) -> None:
        self._credentials = credentials

    @overload
    async def post(self, path: str, model: BaseModel) -> Any: ...
    @overload
    async def post(self, path: str, model: BaseModel, response_model: type[T]) -> T: ...

    async def post(
        self, path: str, model: BaseModel, response_model: Optional[type[T]] = None
    ) -> Union[T, Any]:
        """Make a POST request and return parsed response."""
        url = build_url(self.base_url, path)

        data = self.prepare_data(model)
        data = inject_credentials(data, self.credentials)

        req_id = uuid4().hex[:8] if logger.isEnabledFor(logging.DEBUG) else None
        start = perf_counter() if req_id else 0.0
        if req_id:
            body_keys = sorted(k for k in data.keys() if k != "credentials")
            pre_log(url, body_keys, req_id)

        with map_httpx_exceptions(req_id, path):
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

            if response.status_code >= 400:
                handle_http_error(response, req_id, path)

            json_data = parse_json_or_raise(response, path, req_id)

            handle_api_errors(json_data, req_id, path)

            if req_id:
                post_log(url, response, start, req_id)

            return (
                response_model.model_validate(json_data)
                if response_model
                else json_data
            )

    async def _make_request(self, url: str, data: dict[str, Any]) -> httpx.Response:
        resp = await self.client.post(url, json=data, headers=self.headers)
        raise_if_retryable_status(resp, should_retry_status)
        return resp

    async def aclose(self) -> None:
        if self._owns_client and not self.client.is_closed:
            await self.client.aclose()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("%s HTTP client closed", self.__class__.__name__)

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()
