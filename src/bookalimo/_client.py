"""
Base HTTP client for Book-A-Limo API.
Handles authentication, headers, and common request/response patterns.
"""

from enum import Enum
from functools import lru_cache
from typing import Any, Optional, cast

import httpx
from pydantic import BaseModel

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

    async def _make_request(
        self,
        endpoint: str,
        data: BaseModel,
        model: type[BaseModel],
        timeout: Optional[float] = None,
    ) -> BaseModel:
        """
        Make a POST request to the API with proper error handling.

        Args:
            endpoint: API endpoint (e.g., "/booking/reservation/list/")
            data: Request payload as dict or Pydantic model
            model: Pydantic model to parse the response into
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response as pydantic model

        Raises:
            BookALimoError: On API errors or HTTP errors
        """
        url = f"{self.base_url}{endpoint}"

        # Convert model data to API format
        api_data = self._convert_model_to_api_dict(data.model_dump())

        # Remove None values to avoid API issues
        api_data = self._remove_none_values(api_data)
        api_data = self.handle_enums(api_data)

        try:
            response = await self.client.post(
                url,
                json=api_data,
                headers=self.headers,
                timeout=timeout or self.http_timeout,
            )
            response.raise_for_status()

            # Handle different HTTP status codes
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                raise BookALimoError(
                    error_msg,
                    status_code=response.status_code,
                    response_data={"raw_response": response.text},
                )

            try:
                json_data = response.json()
            except ValueError as e:
                raise BookALimoError(f"Invalid JSON response: {str(e)}") from e

            # Check for API-level errors
            if isinstance(json_data, dict):
                if "error" in json_data and json_data["error"]:
                    raise BookALimoError(
                        f"API Error: {json_data['error']}", response_data=json_data
                    )

                # Check success flag if present
                if "success" in json_data and not json_data["success"]:
                    error_msg = json_data.get("error", "Unknown API error")
                    raise BookALimoError(
                        f"API Error: {error_msg}", response_data=json_data
                    )

            # Convert response back to model format
            return model.model_validate(self._convert_api_to_model_dict(json_data))

        except httpx.TimeoutException:
            raise BookALimoError(
                f"Request timeout after {timeout or self.http_timeout}s"
            ) from None
        except httpx.ConnectError:
            raise BookALimoError(
                "Connection error - unable to reach Book-A-Limo API"
            ) from None
        except httpx.HTTPError as e:
            raise BookALimoError(f"HTTP Error: {str(e)}") from e
        except BookALimoError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            raise BookALimoError(f"Unexpected error: {str(e)}") from e

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
