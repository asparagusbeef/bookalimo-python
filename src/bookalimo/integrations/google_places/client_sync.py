from __future__ import annotations

from collections.abc import Sequence
from os import getenv
from typing import Any, Optional, TypeVar, cast

import httpx
from google.api_core import exceptions as gexc
from google.api_core.client_options import ClientOptions
from google.maps.places_v1 import PlacesClient
from typing_extensions import ParamSpec

from ...exceptions import BookalimoError
from ...logging import get_logger
from ...schemas.places import google as models
from .common import DEFAULT_PLACE_FIELDS, fmt_exc, mask_header
from .proto_adapter import validate_proto_to_model

logger = get_logger("places")

P = ParamSpec("P")
R = TypeVar("R")


class GooglePlaces:
    """
    Google Places API synchronous client for address validation, geocoding, and autocomplete.
    Provides location resolution services that integrate seamlessly with
    Book-A-Limo location factory functions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[PlacesClient] = None,
        http_client: Optional[httpx.Client] = None,
    ):
        """
        Initialize Google Places client.
        Args:
            api_key: Google Places API key. If not provided, it will be read from the GOOGLE_PLACES_API_KEY environment variable.
            client: Optional `PlacesClient` instance.
            http_client: Optional `httpx.Client` instance.
        """
        self.http_client = http_client or httpx.Client()
        if client:
            self.client = client
        else:
            api_key = api_key or getenv("GOOGLE_PLACES_API_KEY")
            if not api_key:
                raise ValueError("Google Places API key is required.")
            self.client = PlacesClient(
                client_options=ClientOptions(api_key=api_key),
            )

    def __enter__(self) -> GooglePlaces:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[BaseException],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close underlying transports safely."""
        try:
            self.client.transport.close()
        finally:
            self.http_client.close()

    def autocomplete(
        self, request: models.AutocompletePlacesRequest, **kwargs: Any
    ) -> models.AutocompletePlacesResponse:
        """
        Get autocomplete suggestions for a location query.
        Args:
            request: AutocompletePlacesRequest object.
            **kwargs: Additional parameters for the Google Places Autocomplete API.
        Returns:
            `AutocompletePlacesResponse` object.
        Raises:
            BookalimoError: If the API request fails.
        """
        try:
            proto = self.client.autocomplete_places(
                request=request.model_dump(), **kwargs
            )
            return validate_proto_to_model(proto, models.AutocompletePlacesResponse)
        except gexc.GoogleAPICallError as e:
            msg = f"Google Places Autocomplete failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e

    def geocode(self, request: models.GeocodingRequest) -> dict[str, Any]:
        try:
            r = self.http_client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=request.to_query_params(),
            )
            r.raise_for_status()
            return cast(dict[str, Any], r.json())
        except httpx.HTTPError as e:
            msg = f"HTTP geocoding failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e

    def search(
        self,
        query: str,
        *,
        fields: Sequence[str] | str = DEFAULT_PLACE_FIELDS,
        **kwargs: Any,
    ) -> list[models.Place]:
        """
        Search for places using a text query.
        Args:
            query: The text query to search for.
            **kwargs: Additional parameters for the Text Search API.
        Returns:
            list[google.maps.places_v1.types.Place]
        Raises:
            BookalimoError: If the API request fails.
        """
        metadata = mask_header(fields)
        try:
            protos = self.client.search_text(
                request={"text_query": query, **kwargs},
                metadata=metadata,
            )
            return [
                validate_proto_to_model(proto, models.Place) for proto in protos.places
            ]
        except gexc.InvalidArgument as e:
            # Often caused by missing/invalid field mask
            msg = f"Google Places Text Search invalid argument: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e
        except gexc.GoogleAPICallError as e:
            msg = f"Google Places Text Search failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e

    def get(
        self,
        place_id: models.GetPlaceRequest,
        *,
        fields: Sequence[str] | str = DEFAULT_PLACE_FIELDS,
        **kwargs: Any,
    ) -> Optional[models.Place]:
        """
        Get details for a specific place.
        Args:
            place_id: The ID of the place to retrieve details for.
            **kwargs: Additional parameters for the Get Place API.
        Returns:
            A `google.maps.places_v1.types.Place` object or `None` if not found.
        Raises:
            BookalimoError: If the API request fails.
        """
        metadata = mask_header(fields)
        try:
            proto = self.client.get_place(
                request={"name": f"places/{place_id}", **kwargs},
                metadata=metadata,
            )
            return validate_proto_to_model(proto, models.Place)
        except gexc.NotFound:
            return None
        except gexc.InvalidArgument as e:
            msg = f"Google Places Get Place invalid argument: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e
        except gexc.GoogleAPICallError as e:
            msg = f"Google Places Get Place failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e
