from __future__ import annotations

from os import getenv
from types import TracebackType
from typing import Any, Optional, TypeVar, cast

import httpx
from google.api_core import exceptions as gexc
from google.maps.places_v1 import PlacesAsyncClient
from typing_extensions import ParamSpec

from ...exceptions import BookalimoError
from ...logging import get_logger
from ...schemas.places import FieldMaskInput
from ...schemas.places import google as models
from .common import (
    DEFAULT_PLACE_FIELDS,
    build_get_place_request,
    build_search_request_params,
    derive_effective_query,
    fmt_exc,
    mask_header,
    normalize_place_from_proto,
    normalize_search_results,
    validate_autocomplete_inputs,
    validate_resolve_airport_inputs,
)
from .proto_adapter import validate_proto_to_model
from .resolve_airport import resolve_airport
from .transports import GoogleAsyncTransport

logger = get_logger("places")

P = ParamSpec("P")
R = TypeVar("R")


class AsyncGooglePlaces:
    """
    Google Places API asynchronous client for address validation, geocoding, and autocomplete.
    Provides location resolution services that integrate seamlessly with
    Book-A-Limo location factory functions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[PlacesAsyncClient] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize Google Places client.
        Args:
            api_key: Google Places API key. If not provided, it will be read from the GOOGLE_PLACES_API_KEY environment variable.
            client: Optional `PlacesAsyncClient` instance.
            http_client: Optional `httpx.AsyncClient` instance.
        """
        self.http_client = http_client or httpx.AsyncClient()
        api_key = api_key or getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise ValueError("Google Places API key is required.")
        self.transport = GoogleAsyncTransport(api_key, client)

    async def __aenter__(self) -> AsyncGooglePlaces:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close underlying transports safely."""
        try:
            await self.transport.close()
        finally:
            await self.http_client.aclose()

    async def autocomplete(
        self,
        input: Optional[str] = None,
        *,
        request: Optional[models.AutocompletePlacesRequest] = None,
    ) -> models.AutocompletePlacesResponse:
        """
        Get autocomplete suggestions for a location query.
        Args:
            input: The text string on which to search.
            request: AutocompletePlacesRequest object.
        Returns:
            `AutocompletePlacesResponse` object.
        Note:
            If both input and request are provided, request will be used.
        Raises:
            ValueError: If neither input nor request is provided, or if both are provided.
            BookalimoError: If the API request fails.
        """
        request = validate_autocomplete_inputs(input, request)
        try:
            proto = await self.transport.autocomplete_places(
                request=request.model_dump()
            )
            return validate_proto_to_model(proto, models.AutocompletePlacesResponse)
        except gexc.GoogleAPICallError as e:
            msg = f"Google Places Autocomplete failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e

    async def geocode(self, request: models.GeocodingRequest) -> dict[str, Any]:
        try:
            r = await self.http_client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=request.to_query_params(),
            )
            r.raise_for_status()
            return cast(dict[str, Any], r.json())
        except httpx.HTTPError as e:
            msg = f"HTTP geocoding failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e

    async def search(
        self,
        query: Optional[str] = None,
        *,
        request: Optional[models.SearchTextRequest] = None,
        fields: FieldMaskInput = DEFAULT_PLACE_FIELDS,
        **kwargs: Any,
    ) -> list[models.Place]:
        """
        Search for places using a text query or SearchTextRequest.
        Args:
            query: Simple text query to search for. Either query or request must be provided.
            request: SearchTextRequest object with advanced search parameters. Either query or request must be provided.
            fields: Field mask for response data.
            **kwargs: Additional parameters for the Text Search API.
        Returns:
            list[models.Place]
        Raises:
            BookalimoError: If the API request fails.
            ValueError: If neither query nor request is provided, or if both are provided.
        """
        request_params = build_search_request_params(query, request, **kwargs)
        metadata = mask_header(fields, prefix="places")

        try:
            protos = await self.transport.search_text(
                request=request_params,
                metadata=metadata,
            )
            return normalize_search_results(protos)
        except gexc.InvalidArgument as e:
            # Often caused by missing/invalid field mask
            msg = f"Google Places Text Search invalid argument: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e
        except gexc.GoogleAPICallError as e:
            msg = f"Google Places Text Search failed: {fmt_exc(e)}"
            logger.error(msg)
            raise BookalimoError(msg) from e

    async def get(
        self,
        place_id: Optional[str] = None,
        *,
        request: Optional[models.GetPlaceRequest] = None,
        fields: FieldMaskInput = DEFAULT_PLACE_FIELDS,
    ) -> Optional[models.Place]:
        """
        Get details for a specific place.
        Args:
            place_id: The ID of the place to retrieve details for.
            request: GetPlaceRequest object with place resource name.
            fields: Optional field mask for response data.
        Returns:
            A models.Place object or None if not found.
        Raises:
            ValueError: If neither place_id nor request is provided.
            BookalimoError: If the API request fails.
        """
        request_params = build_get_place_request(place_id, request)
        metadata = mask_header(fields)

        try:
            proto = await self.transport.get_place(
                request=request_params,
                metadata=metadata,
            )
            return normalize_place_from_proto(proto)
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

    async def resolve_airport(
        self,
        query: Optional[str] = None,
        place_id: Optional[str] = None,
        places: Optional[list[models.Place]] = None,
        max_distance_km: Optional[float] = 100,
        max_results: Optional[int] = 5,
        confidence_threshold: Optional[float] = 0.5,
        text_weight: float = 0.5,
    ) -> list[models.ResolvedAirport]:
        """
        Resolve airport candidates given either a natural language text query, a place_id, or a list of Places.

        Args:
            query: Text query for airport search (optional)
            place_id: Google place ID for proximity matching (optional)
            places: List of existing Place objects for proximity matching (optional)
            max_distance_km: Maximum distance for proximity matching (default: 100km)
            max_results: Maximum number of results to return (default: 5)
            confidence_threshold: Minimum confidence threshold (default: 0.5)
            text_weight: Weight for text search (default: 0.5) If 0.0, only proximity will be used. If 1.0, only text will be used.

        Rules:
        - Provide at most one of {place_id, places}. (query may accompany either.)
        - If nothing but query is given, search for places from the query.
        - If place_id is given:
            * Fetch the place.
            * If no explicit query, derive it from the place's display name.
        - If places is given:
            * If len(places) == 0 and no query, error.
            * If len(places) == 1 and no query, derive query from that place's display name.
            * If len(places) > 1 and no query, error (need query to disambiguate).
        - If nothing is provided, error.
        - If max_distance_km is provided, it must be > 0.

        Returns:
            list[models.ResolvedAirport]
        Raises:
            ValueError on invalid inputs.
            BookalimoError if underlying API requests fail.
        """
        # Validate inputs
        validate_resolve_airport_inputs(place_id, places, max_distance_km)

        # Establish the authoritative places list
        effective_places: list[models.Place]

        if place_id is not None:
            place = await self.get(place_id=place_id)
            if place is None:
                raise ValueError(f"Place with id {place_id!r} was not found.")
            effective_places = [place]

        elif places is not None:
            if len(places) == 0 and (query is None or not str(query).strip()):
                raise ValueError(
                    "Empty 'places' and no 'query' provided; nothing to resolve."
                )
            effective_places = places

        else:
            # Neither place_id nor places: fall back to query-driven search
            if query is None or not str(query).strip():
                raise ValueError("Either place_id, places, or query must be provided.")
            effective_places = await self.search(
                request=models.SearchTextRequest(
                    text_query=str(query).strip(),
                    max_result_count=5,
                )
            )

        # Derive effective query
        effective_query = derive_effective_query(query, effective_places)

        google_places = [
            p.google_place for p in effective_places if p.google_place is not None
        ]

        return resolve_airport(
            effective_query,
            google_places,
            max_distance_km,
            max_results,
            confidence_threshold,
            text_weight,
        )
