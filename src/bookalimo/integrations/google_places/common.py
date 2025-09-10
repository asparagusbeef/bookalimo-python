"""
Common utilities and shared functionality for Google Places clients.
"""

from __future__ import annotations

import re
from typing import Any, Awaitable, Callable, Optional, cast

import httpx
from google.api_core import exceptions as gexc

from ...exceptions import BookalimoError
from ...logging import get_logger
from ...schemas.places import (
    AddressComponent,
    AddressDescriptor,
    FieldMaskInput,
    GooglePlace,
    Place,
    PlaceType,
    RankPreference,
    compile_field_mask,
)
from ...schemas.places import (
    google as models,
)
from .proto_adapter import validate_proto_to_model
from .resolve_airport import resolve_airport

logger = get_logger("places")

# Type variables for shared functionality

# Default field mask for places queries
DEFAULT_PLACE_FIELDS = (
    "display_name",
    "formatted_address",
    "location",
)

ADDRESS_TYPES = {
    "street_address",
    "route",
    "intersection",
    "premise",
    "subpremise",
    "plus_code",
    "postal_code",
    "locality",
    "sublocality",
    "neighborhood",
    "administrative_area_level_1",
    "administrative_area_level_2",
    "country",
    "floor",
    "room",
}


def _fmt_exc(e: BaseException) -> str:
    """Format exception for logging without touching non-existent attributes."""
    return f"{type(e).__name__}: {e}"


def _mask_header(
    fields: FieldMaskInput, prefix: str = ""
) -> tuple[tuple[str, str], ...]:
    """
    Build the X-Goog-FieldMask header. Pass a comma-separated string or a sequence.
    If None, no header is added (e.g., autocomplete, get_photo_media).
    """
    if fields is None:
        return ()  # type: ignore[unreachable]
    value = compile_field_mask(fields, prefix=prefix)
    return (("x-goog-fieldmask", ",".join(value)),)


def strip_html(s: str) -> str:
    # Simple fallback for adr_format_address (which is HTML)
    return re.sub(r"<[^>]+>", "", s) if s else s


def infer_place_type(m: GooglePlace) -> PlaceType:
    # 1) Airport wins outright
    tset = set(m.types or [])
    ptype = (m.primary_type or "").lower() if getattr(m, "primary_type", None) else ""
    if "airport" in tset or ptype == "airport":
        return PlaceType.AIRPORT
    # 2) Anything that looks like a geocoded address
    if tset & ADDRESS_TYPES:
        return PlaceType.ADDRESS
    # 3) Otherwise treat as a point of interest
    return PlaceType.POI


def get_lat_lng(model: GooglePlace) -> tuple[float, float]:
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


def name_from_place(p: Place) -> Optional[str]:
    # Try common fields; support Google Places v1 structure where display_name may have `.text`
    gp = getattr(p, "google_place", None)
    candidates = [
        getattr(gp, "display_name", None),
        getattr(gp, "name", None),
        getattr(p, "name", None),
        getattr(p, "address_descriptor", None),
        getattr(p, "address_components", None),
        getattr(p, "formatted_address", None),
    ]
    for c in candidates:
        if not c:
            continue

        maybe_text = getattr(c, "text", c)
        if isinstance(maybe_text, str) and maybe_text.strip():
            return maybe_text.strip()
        elif isinstance(maybe_text, AddressDescriptor):
            return maybe_text.landmarks[0].display_name.text
        elif isinstance(maybe_text, list):
            for item in maybe_text:
                if isinstance(item, AddressComponent):
                    return item.long_text
                else:
                    break
    return None


def _build_search_request_params(
    query: Optional[str],
    request: Optional[models.SearchTextRequest],
    **kwargs: Any,
) -> dict[str, Any]:
    """Build request parameters for search_text API call."""
    if query is None and request is None:
        raise ValueError("Either 'query' or 'request' must be provided")
    if query is not None and request is not None:
        raise ValueError(
            "Only one of 'query' or 'request' should be provided, not both"
        )

    if request is not None:
        request_params = request.model_dump(exclude_none=True)
        request_params.update(kwargs)
        return request_params
    else:
        return {"text_query": query, **kwargs}


def _normalize_place_from_proto(proto: Any) -> models.Place:
    """Convert a proto Place to our normalized Place model."""

    model = validate_proto_to_model(proto, GooglePlace)
    adr_format = getattr(model, "adr_format_address", None)
    addr = (
        getattr(model, "formatted_address", None)
        or getattr(model, "short_formatted_address", None)
        or strip_html(adr_format or "")
        or ""
    )
    lat, lng = get_lat_lng(model)
    return models.Place(
        formatted_address=addr,
        lat=lat,
        lng=lng,
        place_type=infer_place_type(model),
        google_place=model,
    )


def _normalize_search_results(proto_response: Any) -> list[models.Place]:
    """Convert search_text response to list of normalized Place models."""
    return [_normalize_place_from_proto(proto) for proto in proto_response.places]


def _build_get_place_request(
    place_id: Optional[str], request: Optional[models.GetPlaceRequest]
) -> dict[str, Any]:
    """Build request parameters for get_place API call."""
    if place_id is None and request is None:
        raise ValueError("Either 'place_id' or 'request' must be provided")

    if request:
        return request.model_dump(exclude_none=True, context={"enum_out": "name"})
    else:
        return {"name": f"places/{place_id}"}


def _derive_effective_query(query: Optional[str], places: list[models.Place]) -> str:
    """Derive an effective query string from query and/or places."""
    effective_query = (query or "").strip()

    if not effective_query:
        if len(places) == 1:
            derived = name_from_place(places[0])
            if not derived:
                raise ValueError("Could not derive a query from the provided place.")
            effective_query = derived
        else:
            raise ValueError(
                "Multiple places provided but no 'query' to disambiguate them."
            )

    return effective_query


def _validate_resolve_airport_inputs(
    place_id: Optional[str],
    places: Optional[list[models.Place]],
    max_distance_km: Optional[float],
) -> None:
    """Validate inputs for resolve_airport method."""
    if place_id is not None and places is not None:
        raise ValueError("Provide only one of place_id or places, not both.")
    if max_distance_km is not None and max_distance_km <= 0:
        raise ValueError("max_distance_km, if provided, must be > 0.")


def validate_autocomplete_inputs(
    input: Optional[str],
    request: Optional[models.AutocompletePlacesRequest],
) -> models.AutocompletePlacesRequest:
    """Validate inputs for autocomplete method."""
    if request is None:
        if input is None:
            raise ValueError("Either input or request must be provided.")
        else:
            request = models.AutocompletePlacesRequest(input=input)
    return request


def _call_gplaces_sync(
    ctx: str,
    fn: Callable[..., Any],
    *args: Any,
    not_found_ok: bool = False,
    **kwargs: Any,
) -> Any:
    try:
        return fn(*args, **kwargs)
    except gexc.NotFound:
        if not_found_ok:
            return None
        raise BookalimoError(f"{ctx} not found") from None
    except gexc.InvalidArgument as e:
        msg = f"{ctx} invalid argument: {_fmt_exc(e)}"
        logger.error(msg)
        raise BookalimoError(msg) from e
    except gexc.GoogleAPICallError as e:
        msg = f"{ctx} failed: {_fmt_exc(e)}"
        logger.error(msg)
        raise BookalimoError(msg) from e


async def _call_gplaces_async(
    ctx: str,
    fn: Callable[..., Awaitable[Any]],
    *args: Any,
    not_found_ok: bool = False,
    **kwargs: Any,
) -> Any:
    try:
        return await fn(*args, **kwargs)
    except gexc.NotFound:
        if not_found_ok:
            return None
        raise BookalimoError(f"{ctx} not found") from None
    except gexc.InvalidArgument as e:
        msg = f"{ctx} invalid argument: {_fmt_exc(e)}"
        logger.error(msg)
        raise BookalimoError(msg) from e
    except gexc.GoogleAPICallError as e:
        msg = f"{ctx} failed: {_fmt_exc(e)}"
        logger.error(msg)
        raise BookalimoError(msg) from e


def handle_autocomplete_impl(
    transport_call: Callable[[dict[str, Any]], Any],
    request: models.AutocompletePlacesRequest,
) -> models.AutocompletePlacesResponse:
    """Shared implementation for autocomplete method."""

    proto = _call_gplaces_sync(
        "Google Places Autocomplete", transport_call, request.model_dump()
    )
    return validate_proto_to_model(proto, models.AutocompletePlacesResponse)


def prepare_geocode_params(
    request: models.GeocodingRequest,
    api_key: str,
) -> Any:
    """Prepare geocode parameters for both sync/async."""
    params = request.to_query_params()
    params = params.add("key", api_key)
    return params


def handle_geocode_response(response: Any) -> dict[str, Any]:
    """Handle geocode response for both sync/async."""
    try:
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
    except httpx.HTTPError as e:
        msg = f"HTTP geocoding failed: {_fmt_exc(e)}"
        logger.error(msg)
        raise BookalimoError(msg) from e


async def handle_autocomplete_impl_async(
    transport_call: Callable[[dict[str, Any]], Awaitable[Any]],
    request: models.AutocompletePlacesRequest,
) -> models.AutocompletePlacesResponse:
    """Shared implementation for async autocomplete method."""

    proto = await _call_gplaces_async(
        "Google Places Autocomplete", transport_call, request.model_dump()
    )
    return validate_proto_to_model(proto, models.AutocompletePlacesResponse)


def handle_search_impl(
    transport_call: Callable[[dict[str, Any], tuple[tuple[str, str], ...]], Any],
    query: Optional[str] = None,
    request: Optional[models.SearchTextRequest] = None,
    fields: FieldMaskInput = DEFAULT_PLACE_FIELDS,
    **kwargs: Any,
) -> list[models.Place]:
    """Shared implementation for search method."""
    request_params, metadata = _prepare_search_params_and_metadata(
        query, request, fields, **kwargs
    )

    protos = _call_gplaces_sync(
        "Google Places Text Search", transport_call, request_params, metadata
    )
    return _normalize_search_results(protos)


async def handle_search_impl_async(
    transport_call: Callable[
        [dict[str, Any], tuple[tuple[str, str], ...]], Awaitable[Any]
    ],
    query: Optional[str] = None,
    request: Optional[models.SearchTextRequest] = None,
    fields: FieldMaskInput = DEFAULT_PLACE_FIELDS,
    **kwargs: Any,
) -> list[models.Place]:
    """Shared implementation for async search method."""
    request_params, metadata = _prepare_search_params_and_metadata(
        query, request, fields, **kwargs
    )

    protos = await _call_gplaces_async(
        "Google Places Text Search", transport_call, request_params, metadata
    )
    return _normalize_search_results(protos)


def handle_get_place_impl(
    transport_call: Callable[[dict[str, Any], tuple[tuple[str, str], ...]], Any],
    place_id: Optional[str] = None,
    request: Optional[models.GetPlaceRequest] = None,
    fields: FieldMaskInput = DEFAULT_PLACE_FIELDS,
) -> Optional[models.Place]:
    """Shared implementation for get place method."""
    request_params, metadata = _prepare_get_params_and_metadata(
        place_id, request, fields
    )

    proto = _call_gplaces_sync(
        "Google Places Get Place",
        transport_call,
        request_params,
        metadata,
        not_found_ok=True,
    )
    return None if proto is None else _normalize_place_from_proto(proto)


async def handle_get_place_impl_async(
    transport_call: Callable[
        [dict[str, Any], tuple[tuple[str, str], ...]], Awaitable[Any]
    ],
    place_id: Optional[str] = None,
    request: Optional[models.GetPlaceRequest] = None,
    fields: FieldMaskInput = DEFAULT_PLACE_FIELDS,
) -> Optional[models.Place]:
    """Shared implementation for async get place method."""
    request_params, metadata = _prepare_get_params_and_metadata(
        place_id, request, fields
    )

    proto = await _call_gplaces_async(
        "Google Places Get Place",
        transport_call,
        request_params,
        metadata,
        not_found_ok=True,
    )
    return None if proto is None else _normalize_place_from_proto(proto)


def _prepare_search_params_and_metadata(
    query: Optional[str],
    request: Optional[models.SearchTextRequest],
    fields: FieldMaskInput,
    **kwargs: Any,
) -> tuple[dict[str, Any], tuple[tuple[str, str], ...]]:
    """Prepare search parameters and metadata for both sync/async."""
    request_params = _build_search_request_params(query, request, **kwargs)
    metadata = _mask_header(fields, prefix="places")
    return request_params, metadata


def _prepare_get_params_and_metadata(
    place_id: Optional[str],
    request: Optional[models.GetPlaceRequest],
    fields: FieldMaskInput,
) -> tuple[dict[str, Any], tuple[tuple[str, str], ...]]:
    """Prepare get place parameters and metadata for both sync/async."""
    request_params = _build_get_place_request(place_id, request)
    metadata = _mask_header(fields)
    return request_params, metadata


def create_search_text_request(
    query: str,
    region_code: Optional[str],
) -> models.SearchTextRequest:
    return models.SearchTextRequest(
        text_query=query,
        region_code=region_code,
        max_result_count=5,
        rank_preference=RankPreference.RELEVANCE,
        # included_type="airport",
        strict_type_filtering=False,
    )


def handle_resolve_airport_preprocessing(
    query: Optional[str],
    place_id: Optional[str],
    places: Optional[list[models.Place]],
    max_distance_km: Optional[float],
) -> tuple[Optional[str], list[models.Place], bool]:
    """
    Handle the preprocessing logic for resolve_airport that doesn't depend on sync/async.
    Returns (effective_query_or_none, places_to_resolve, needs_search_call).
    If needs_search_call is True, the caller should perform a search using the query.
    """
    # Validate inputs
    _validate_resolve_airport_inputs(place_id, places, max_distance_km)

    # Handle different input scenarios
    if place_id is not None:
        # Caller needs to fetch the place using get()
        return query, [], True  # Signal that caller needs to call get()

    elif places is not None:
        if len(places) == 0 and (query is None or not str(query).strip()):
            raise ValueError(
                "Empty 'places' and no 'query' provided; nothing to resolve."
            )
        return query, places, False

    else:
        # Neither place_id nor places: fall back to query-driven search
        if query is None or not str(query).strip():
            raise ValueError("Either place_id, places, or query must be provided.")
        return query, [], True  # Signal that caller needs to call search()


def handle_resolve_airport_postprocessing(
    query: Optional[str],
    effective_places: list[models.Place],
    max_distance_km: Optional[float],
    max_results: Optional[int],
    confidence_threshold: Optional[float],
    text_weight: float,
) -> list[models.ResolvedAirport]:
    """Handle the final processing logic for resolve_airport."""

    # Derive effective query
    effective_query = _derive_effective_query(query, effective_places)

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
