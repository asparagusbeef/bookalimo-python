from __future__ import annotations

import re
from os import getenv
from types import TracebackType
from typing import Any, Optional, TypeVar, cast

import httpx
from google.api_core import exceptions as gexc
from google.api_core.client_options import ClientOptions
from google.maps.places_v1 import PlacesAsyncClient
from typing_extensions import ParamSpec

from ...exceptions import BookalimoError
from ...logging import get_logger
from ...schemas.places import google as models
from ...schemas.places.place import Place as GooglePlace
from .common import (
    ADDRESS_TYPES,
    DEFAULT_PLACE_FIELDS,
    DEFAULT_PLACE_LIST_FIELDS,
    Fields,
    PlaceListFields,
    fmt_exc,
    mask_header,
)
from .proto_adapter import validate_proto_to_model

logger = get_logger("places")

P = ParamSpec("P")
R = TypeVar("R")


def _strip_html(s: str) -> str:
    # Simple fallback for adr_format_address (which is HTML)
    return re.sub(r"<[^>]+>", "", s) if s else s


def _infer_place_type(m: GooglePlace) -> str:
    # 1) Airport wins outright
    tset = set(m.types or [])
    ptype = (m.primary_type or "").lower() if getattr(m, "primary_type", None) else ""
    if "airport" in tset or ptype == "airport":
        return "airport"
    # 2) Anything that looks like a geocoded address
    if tset & ADDRESS_TYPES:
        return "address"
    # 3) Otherwise treat as a point of interest
    return "poi"


def _get_lat_lng(model: GooglePlace) -> tuple[float, float]:
    if model.location:
        lat = model.location.latitude
        lng = model.location.longitude
    elif model.viewport:
        lat = model.viewport.low.latitude
        lng = model.viewport.low.longitude
    else:
        lat = 0
        lng = 0
    return lat, lng


class AsyncGooglePlaces:
    """
    Google Places API client for address validation, geocoding, and autocomplete.
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
        if client:
            self.client = client
        else:
            api_key = api_key or getenv("GOOGLE_PLACES_API_KEY")
            if not api_key:
                raise ValueError("Google Places API key is required.")
            self.client = PlacesAsyncClient(
                client_options=ClientOptions(api_key=api_key),
            )

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
            await self.client.transport.close()
        finally:
            await self.http_client.aclose()

    async def autocomplete(
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
            proto = await self.client.autocomplete_places(
                request=request.model_dump(), **kwargs
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
        query: str,
        *,
        fields: PlaceListFields = DEFAULT_PLACE_LIST_FIELDS,
        **kwargs: Any,
    ) -> list[models.Place]:
        """
        Search for places using a text query.
        Args:
            query: The text query to search for.
            **kwargs: Additional parameters for the Text Search API.
        Returns:
            list[models.Place]
        Raises:
            BookalimoError: If the API request fails.
        """
        metadata = mask_header(fields)
        try:
            protos = await self.client.search_text(
                request={"text_query": query, **kwargs},
                metadata=metadata,
            )
            pydantic_models = [
                validate_proto_to_model(proto, GooglePlace) for proto in protos.places
            ]
            place_models: list[models.Place] = []
            for model in pydantic_models:
                adr_format = getattr(model, "adr_format_address", None)
                addr = (
                    getattr(model, "formatted_address", None)
                    or getattr(model, "short_formatted_address", None)
                    or _strip_html(adr_format or "")
                    or ""
                )
                lat, lng = _get_lat_lng(model)
                place_models.append(
                    models.Place(
                        formatted_address=addr,
                        lat=lat,
                        lng=lng,
                        place_type=_infer_place_type(model),
                        iata_code=None,
                        google_place=model,
                    )
                )
            return place_models
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
        place_id: models.GetPlaceRequest,
        *,
        fields: Fields = DEFAULT_PLACE_FIELDS,
        **kwargs: Any,
    ) -> Optional[models.Place]:
        """
        Get details for a specific place.
        Args:
            place_id: The ID of the place to retrieve details for.
            **kwargs: Additional parameters for the Get Place API.
        Returns:
            A models.Place object or None if not found.
        Raises:
            BookalimoError: If the API request fails.
        """
        metadata = mask_header(fields)
        try:
            proto = await self.client.get_place(
                request={"name": f"places/{place_id}", **kwargs},
                metadata=metadata,
            )
            # Convert proto to GooglePlace first, then process like search
            model = validate_proto_to_model(proto, GooglePlace)
            adr_format = getattr(model, "adr_format_address", None)
            addr = (
                getattr(model, "formatted_address", None)
                or getattr(model, "short_formatted_address", None)
                or _strip_html(adr_format or "")
                or ""
            )
            lat, lng = _get_lat_lng(model)
            return models.Place(
                formatted_address=addr,
                lat=lat,
                lng=lng,
                place_type=_infer_place_type(model),
                iata_code=None,
                google_place=model,
            )
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
