"""
Common utilities and shared functionality for Google Places clients.
"""

from __future__ import annotations

from typing import Literal, Sequence, Union

from ...logging import get_logger

logger = get_logger("places")


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
