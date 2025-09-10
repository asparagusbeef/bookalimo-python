from __future__ import annotations

from os import getenv
from types import TracebackType
from typing import Any, Optional, TypeVar

import httpx
from google.maps.places_v1 import PlacesClient
from typing_extensions import ParamSpec

from ...logging import get_logger
from ...schemas.places import FieldMaskInput
from ...schemas.places import google as models
from .common import (
    DEFAULT_PLACE_FIELDS,
    create_search_text_request,
    handle_autocomplete_impl,
    handle_geocode_response,
    handle_get_place_impl,
    handle_resolve_airport_postprocessing,
    handle_resolve_airport_preprocessing,
    handle_search_impl,
    prepare_geocode_params,
    validate_autocomplete_inputs,
)
from .transports import GoogleSyncTransport

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
        self.api_key = api_key or getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("Google Places API key is required.")
        self.transport = GoogleSyncTransport(self.api_key, client)

    def __enter__(self) -> GooglePlaces:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close underlying transports safely."""
        try:
            self.transport.close()
        finally:
            self.http_client.close()

    def autocomplete(
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
        return handle_autocomplete_impl(
            lambda req: self.transport.autocomplete_places(request=req),
            request,
        )

    def geocode(self, request: models.GeocodingRequest) -> dict[str, Any]:
        assert self.api_key is not None  # Validated in __init__
        params = prepare_geocode_params(request, self.api_key)
        r = self.http_client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params=params,
        )
        return handle_geocode_response(r)

    def search(
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
        return handle_search_impl(
            lambda req, meta: self.transport.search_text(request=req, metadata=meta),
            query,
            request,
            fields,
            **kwargs,
        )

    def get(
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
        return handle_get_place_impl(
            lambda req, meta: self.transport.get_place(request=req, metadata=meta),
            place_id,
            request,
            fields,
        )

    def resolve_airport(
        self,
        query: Optional[str] = None,
        place_id: Optional[str] = None,
        places: Optional[list[models.Place]] = None,
        country_code: Optional[str] = None,
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
            country_code: Country code for proximity matching (optional)
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
        # Handle preprocessing that doesn't depend on sync/async
        preprocessed_query, preprocessed_places, needs_call = (
            handle_resolve_airport_preprocessing(
                query, place_id, places, max_distance_km
            )
        )

        # Handle the calls that do depend on sync/async
        effective_places: list[models.Place]
        if place_id is not None:
            place = self.get(place_id=place_id)
            if place is None:
                raise ValueError(f"Place with id {place_id!r} was not found.")
            effective_places = [place]
        elif needs_call and preprocessed_places == []:
            # Need to perform search
            effective_places = self.search(
                request=create_search_text_request(
                    query=str(preprocessed_query).strip(),
                    region_code=country_code,
                )
            )
        else:
            effective_places = preprocessed_places

        # Handle postprocessing
        return handle_resolve_airport_postprocessing(
            preprocessed_query,
            effective_places,
            max_distance_km,
            max_results,
            confidence_threshold,
            text_weight,
        )
