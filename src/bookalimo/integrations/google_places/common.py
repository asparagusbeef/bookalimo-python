"""
Common utilities and shared functionality for Google Places clients.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional, Sequence, Union

from ...logging import get_logger
from ...schemas.places import (
    AddressComponent,
    AddressDescriptor,
    GooglePlace,
    Place,
    PlaceType,
)
from ...schemas.places import (
    google as models,
)

logger = get_logger("places")

# Default field mask for places queries
DEFAULT_PLACE_FIELDS: Fields = (
    "display_name",
    "formatted_address",
    "location",
)

DEFAULT_PLACE_LIST_FIELDS: PlaceListFields = (
    "places.display_name",
    "places.formatted_address",
    "places.location",
)


Fields = Union[
    str,
    Sequence[
        Literal[
            "*",
            # Identity
            "name",
            # Labels & typing
            "display_name",
            "types",
            "primary_type",
            "primary_type_display_name",
            # Phones & addresses
            "national_phone_number",
            "international_phone_number",
            "formatted_address",
            "short_formatted_address",
            "postal_address",
            "address_components",
            "plus_code",
            # Location & map
            "location",
            "viewport",
            # Scores, links, media
            "rating",
            "google_maps_uri",
            "website_uri",
            "reviews",
            "photos",
            # Hours
            "regular_opening_hours",
            "current_opening_hours",
            "current_secondary_opening_hours",
            "regular_secondary_opening_hours",
            "utc_offset_minutes",
            "time_zone",
            # Misc attributes
            "adr_format_address",
            "business_status",
            "price_level",
            "attributions",
            "user_rating_count",
            "icon_mask_base_uri",
            "icon_background_color",
            # Food/venue features
            "takeout",
            "delivery",
            "dine_in",
            "curbside_pickup",
            "reservable",
            "serves_breakfast",
            "serves_lunch",
            "serves_dinner",
            "serves_beer",
            "serves_wine",
            "serves_brunch",
            "serves_vegetarian_food",
            "outdoor_seating",
            "live_music",
            "menu_for_children",
            "serves_cocktails",
            "serves_dessert",
            "serves_coffee",
            "good_for_children",
            "allows_dogs",
            "restroom",
            "good_for_groups",
            "good_for_watching_sports",
            # Options & related places
            "payment_options",
            "parking_options",
            "sub_destinations",
            "accessibility_options",
            # Fuel/EV & AI summaries
            "fuel_options",
            "ev_charge_options",
            "generative_summary",
            "review_summary",
            "ev_charge_amenity_summary",
            "neighborhood_summary",
            # Context
            "containing_places",
            "pure_service_area_business",
            "address_descriptor",
            "price_range",
            # Missing in your model but present in proto
            "editorial_summary",
        ]
    ],
]

PlaceListFields = Union[
    str,
    Sequence[
        Literal[
            "*",
            # Identity
            "places.name",
            # Labels & typing
            "places.display_name",
            "places.types",
            "places.primary_type",
            "places.primary_type_display_name",
            # Phones & addresses
            "places.national_phone_number",
            "places.international_phone_number",
            "places.formatted_address",
            "places.short_formatted_address",
            "places.postal_address",
            "places.address_components",
            "places.plus_code",
            # Location & map
            "places.location",
            "places.viewport",
            # Scores, links, media
            "places.rating",
            "places.google_maps_uri",
            "places.website_uri",
            "places.reviews",
            "places.photos",
            # Hours
            "places.regular_opening_hours",
            "places.current_opening_hours",
            "places.current_secondary_opening_hours",
            "places.regular_secondary_opening_hours",
            "places.utc_offset_minutes",
            "places.time_zone",
            # Misc attributes
            "places.adr_format_address",
            "places.business_status",
            "places.price_level",
            "places.attributions",
            "places.user_rating_count",
            "places.icon_mask_base_uri",
            "places.icon_background_color",
            # Food/venue features
            "places.takeout",
            "places.delivery",
            "places.dine_in",
            "places.curbside_pickup",
            "places.reservable",
            "places.serves_breakfast",
            "places.serves_lunch",
            "places.serves_dinner",
            "places.serves_beer",
            "places.serves_wine",
            "places.serves_brunch",
            "places.serves_vegetarian_food",
            "places.outdoor_seating",
            "places.live_music",
            "places.menu_for_children",
            "places.serves_cocktails",
            "places.serves_dessert",
            "places.serves_coffee",
            "places.good_for_children",
            "places.allows_dogs",
            "places.restroom",
            "places.good_for_groups",
            "places.good_for_watching_sports",
            # Options & related places
            "places.payment_options",
            "places.parking_options",
            "places.sub_destinations",
            "places.accessibility_options",
            # Fuel/EV & AI summaries
            "places.fuel_options",
            "places.ev_charge_options",
            "places.generative_summary",
            "places.review_summary",
            "places.ev_charge_amenity_summary",
            "places.neighborhood_summary",
            # Context
            "places.containing_places",
            "places.pure_service_area_business",
            "places.address_descriptor",
            "places.price_range",
            # Missing in your model but present in proto
            "places.editorial_summary",
        ]
    ],
]

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


def fmt_exc(e: BaseException) -> str:
    """Format exception for logging without touching non-existent attributes."""
    return f"{type(e).__name__}: {e}"


def mask_header(fields: Sequence[str] | str | None) -> tuple[tuple[str, str], ...]:
    """
    Build the X-Goog-FieldMask header. Pass a comma-separated string or a sequence.
    If None, no header is added (e.g., autocomplete, get_photo_media).
    """
    if fields is None:
        return ()
    if isinstance(fields, str):
        value = fields
    else:
        value = ",".join(fields)
    return (("x-goog-fieldmask", value),)


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


def build_search_request_params(
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


def normalize_place_from_proto(proto: Any) -> models.Place:
    """Convert a proto Place to our normalized Place model."""
    from .proto_adapter import validate_proto_to_model

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


def normalize_search_results(proto_response: Any) -> list[models.Place]:
    """Convert search_text response to list of normalized Place models."""
    return [normalize_place_from_proto(proto) for proto in proto_response.places]


def build_get_place_request(
    place_id: Optional[str], request: Optional[models.GetPlaceRequest]
) -> dict[str, Any]:
    """Build request parameters for get_place API call."""
    if place_id is None and request is None:
        raise ValueError("Either 'place_id' or 'request' must be provided")

    if request:
        return request.model_dump(exclude_none=True)
    else:
        return {"name": f"places/{place_id}"}


def derive_effective_query(query: Optional[str], places: list[models.Place]) -> str:
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


def validate_resolve_airport_inputs(
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
