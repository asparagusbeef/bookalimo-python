"""
Base HTTP client for Book-A-Limo API.
Handles authentication, headers, and common request/response patterns.
"""

import logging
from enum import Enum
from functools import lru_cache
from time import perf_counter
from typing import Any, Optional, TypeVar, cast, overload
from uuid import uuid4

import httpx
from pydantic import BaseModel

from ._logging import get_logger
from .exceptions import BookALimoError
from .models import (
    BookRequest,
    BookResponse,
    Credentials,
    DetailsRequest,
    DetailsResponse,
    EditableReservationRequest,
    EditableReservationRequestAuthenticated,
    EditReservationResponse,
    GetReservationRequest,
    GetReservationResponse,
    ListReservationsRequest,
    ListReservationsResponse,
    PriceRequest,
    PriceRequestAuthenticated,
    PriceResponse,
)

logger = get_logger("client")

T = TypeVar("T")


@lru_cache(maxsize=1)
def get_version() -> str:
    """Get the version of the BookALimo client."""
    from bookalimo import __version__

    return __version__


class BookALimoClient:
    """
    Base HTTP client for Book-A-Limo API.
    Centralizes headers, auth, request helpers, and error handling.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        credentials: Credentials,
        user_agent: str = "bookalimo-python",
        version: Optional[str] = None,
        base_url: str = "https://api.bookalimo.com",
        http_timeout: float = 5.0,
    ):
        """Initialize the client with an HTTP client."""
        self.client = client
        version = version or get_version()
        self.credentials = credentials
        self.headers = {
            "content-type": "application/json",
            "user-agent": f"{user_agent}/{version}",
        }
        self.base_url = base_url
        self.http_timeout = http_timeout
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Client initialized (base_url=%s, timeout=%s, user_agent=%s)",
                self.base_url,
                self.http_timeout,
                self.headers.get("user-agent"),
            )

    def _convert_model_to_api_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert Python model field names to API field names.
        Handles snake_case to camelCase and other API-specific naming.
        """
        converted: dict[str, Any] = {}

        for key, value in data.items():
            # Convert snake_case to camelCase for API
            api_key = self._to_camel_case(key)

            # Handle nested objects
            if isinstance(value, dict):
                converted[api_key] = self._convert_model_to_api_dict(value)
            elif isinstance(value, list):
                converted[api_key] = [
                    (
                        self._convert_model_to_api_dict(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                converted[api_key] = value

        return converted

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        if "_" not in snake_str:
            return snake_str

        components = snake_str.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])

    def _convert_api_to_model_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert API response field names to Python model field names.
        Handles camelCase to snake_case conversion.
        """
        converted: dict[str, Any] = {}

        for key, value in data.items():
            # Convert camelCase to snake_case
            model_key = self._to_snake_case(key)

            # Handle nested objects
            if isinstance(value, dict):
                converted[model_key] = self._convert_api_to_model_dict(value)
            elif isinstance(value, list):
                converted[model_key] = [
                    (
                        self._convert_api_to_model_dict(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                converted[model_key] = value

        return converted

    @overload
    def handle_enums(self, obj: Enum) -> Any: ...
    @overload
    def handle_enums(self, obj: dict[str, Any]) -> dict[str, Any]: ...
    @overload
    def handle_enums(self, obj: list[Any]) -> list[Any]: ...
    @overload
    def handle_enums(self, obj: tuple[Any, ...]) -> tuple[Any, ...]: ...
    @overload
    def handle_enums(self, obj: set[Any]) -> set[Any]: ...
    @overload
    def handle_enums(self, obj: Any) -> Any: ...

    def handle_enums(self, obj: Any) -> Any:
        """
        Simple utility to convert enums to their values for JSON serialization.

        Args:
            obj: Any object that might contain enums

        Returns:
            Object with enums converted to their values
        """
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self.handle_enums(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return type(obj)(self.handle_enums(item) for item in obj)
        elif isinstance(obj, set):
            return {self.handle_enums(item) for item in obj}
        else:
            return obj

    def _to_snake_case(self, camel_str: str) -> str:
        """Convert camelCase to snake_case."""
        result = []
        for i, char in enumerate(camel_str):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)

    def prepare_data(self, data: BaseModel) -> dict[str, Any]:
        """
        Prepare data for API requests by converting it to the appropriate format.

        Args:
            data: The data to prepare, as a Pydantic model instance.

        Returns:
            A dictionary representation of the data, ready for API consumption.
        """
        api_data = self._convert_model_to_api_dict(data.model_dump())
        api_data = self._remove_none_values(api_data)
        api_data = self.handle_enums(api_data)
        return cast(dict[str, Any], api_data)

    async def _make_request(
        self,
        endpoint: str,
        data: BaseModel,
        model: type[BaseModel],
        timeout: Optional[float] = None,
    ) -> BaseModel:
        url = f"{self.base_url}{endpoint}"

        # Convert model data to API format
        api_data = self.prepare_data(data)

        debug_on = logger.isEnabledFor(logging.DEBUG)
        req_id = None
        if debug_on:
            req_id = uuid4().hex[:8]
            start = perf_counter()
            body_keys = sorted(k for k in api_data.keys() if k != "credentials")
            logger.debug(
                "→ [%s] POST %s timeout=%s body_keys=%s",
                req_id,
                endpoint,
                timeout or self.http_timeout,
                body_keys,
            )

        try:
            response = await self.client.post(
                url,
                json=api_data,
                headers=self.headers,
                timeout=timeout or self.http_timeout,
            )
            response.raise_for_status()

            # HTTP 4xx/5xx already raise in httpx, but keep defensive check:
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}"
                if debug_on:
                    logger.warning("× [%s] %s %s", req_id or "-", endpoint, error_msg)
                raise BookALimoError(
                    f"{error_msg}: {response.text}",
                    status_code=response.status_code,
                    response_data={"raw_response": response.text},
                )

            try:
                json_data = response.json()
            except ValueError as e:
                if debug_on:
                    logger.warning("× [%s] %s invalid JSON", req_id or "-", endpoint)
                raise BookALimoError(f"Invalid JSON response: {str(e)}") from e

            # API-level errors
            if isinstance(json_data, dict):
                if json_data.get("error"):
                    if debug_on:
                        logger.warning("× [%s] %s API error", req_id or "-", endpoint)
                    raise BookALimoError(
                        f"API Error: {json_data['error']}", response_data=json_data
                    )
                if "success" in json_data and not json_data["success"]:
                    msg = json_data.get("error", "Unknown API error")
                    if debug_on:
                        logger.warning("× [%s] %s API error", req_id or "-", endpoint)
                    raise BookALimoError(f"API Error: {msg}", response_data=json_data)

            if debug_on:
                dur_ms = (perf_counter() - start) * 1000.0
                reqid_hdr = response.headers.get(
                    "x-request-id"
                ) or response.headers.get("request-id")
                content_len = None
                try:
                    content_len = len(response.content)
                except Exception:
                    pass
                logger.debug(
                    "← [%s] %s %s in %.1f ms len=%s reqid=%s",
                    req_id,
                    response.status_code,
                    endpoint,
                    dur_ms,
                    content_len,
                    reqid_hdr,
                )

            return model.model_validate(self._convert_api_to_model_dict(json_data))

        except httpx.TimeoutException:
            if debug_on:
                logger.warning(
                    "× [%s] %s timeout after %ss",
                    req_id or "-",
                    endpoint,
                    timeout or self.http_timeout,
                )
            raise BookALimoError(
                f"Request timeout after {timeout or self.http_timeout}s"
            ) from None
        except httpx.ConnectError:
            if debug_on:
                logger.warning("× [%s] %s connection error", req_id or "-", endpoint)
            raise BookALimoError(
                "Connection error - unable to reach Book-A-Limo API"
            ) from None
        except httpx.HTTPError as e:
            if debug_on:
                logger.warning(
                    "× [%s] %s HTTP error: %s",
                    req_id or "-",
                    endpoint,
                    e.__class__.__name__,
                )
            raise BookALimoError(f"HTTP Error: {str(e)}") from e
        except BookALimoError:
            # already logged above where relevant
            raise
        except Exception as e:
            if debug_on:
                logger.warning(
                    "× [%s] %s unexpected error: %s",
                    req_id or "-",
                    endpoint,
                    e.__class__.__name__,
                )
            raise BookALimoError(f"Unexpected error: {str(e)}") from e

    @overload
    def _remove_none_values(self, data: dict[str, Any]) -> dict[str, Any]: ...
    @overload
    def _remove_none_values(self, data: list[Any]) -> list[Any]: ...
    @overload
    def _remove_none_values(self, data: Any) -> Any: ...

    def _remove_none_values(self, data: Any) -> Any:
        """Recursively remove None values from data structure."""
        if isinstance(data, dict):
            return {
                k: self._remove_none_values(v) for k, v in data.items() if v is not None
            }
        elif isinstance(data, list):
            return [self._remove_none_values(item) for item in data]
        else:
            return data

    async def list_reservations(
        self, is_archive: bool = False
    ) -> ListReservationsResponse:
        """List reservations for the given credentials."""
        data = ListReservationsRequest(
            credentials=self.credentials, is_archive=is_archive
        )
        return cast(
            ListReservationsResponse,
            await self._make_request(
                "/booking/reservation/list/", data, model=ListReservationsResponse
            ),
        )

    async def get_reservation(self, confirmation: str) -> GetReservationResponse:
        """Get detailed reservation information."""
        data = GetReservationRequest(
            credentials=self.credentials, confirmation=confirmation
        )
        return cast(
            GetReservationResponse,
            await self._make_request(
                "/booking/reservation/get/", data, model=GetReservationResponse
            ),
        )

    async def get_prices(self, price_request: PriceRequest) -> PriceResponse:
        """Get pricing for a trip."""
        price_request_authenticated = PriceRequestAuthenticated(
            credentials=self.credentials, **price_request.model_dump()
        )
        return cast(
            PriceResponse,
            await self._make_request(
                "/booking/price/", price_request_authenticated, model=PriceResponse
            ),
        )

    async def set_details(self, details_request: DetailsRequest) -> DetailsResponse:
        """Set reservation details and get updated pricing."""
        return cast(
            DetailsResponse,
            await self._make_request(
                "/booking/details/", details_request, model=DetailsResponse
            ),
        )

    async def book_reservation(self, book_request: BookRequest) -> BookResponse:
        """Book a reservation."""
        return cast(
            BookResponse,
            await self._make_request(
                "/booking/book/", book_request, model=BookResponse
            ),
        )

    async def edit_reservation(
        self, edit_request: EditableReservationRequest
    ) -> EditReservationResponse:
        """Edit or cancel a reservation."""
        edit_request_authenticated = EditableReservationRequestAuthenticated(
            credentials=self.credentials, **edit_request.model_dump()
        )
        return cast(
            EditReservationResponse,
            await self._make_request(
                "/booking/edit/",
                edit_request_authenticated,
                model=EditReservationResponse,
            ),
        )
