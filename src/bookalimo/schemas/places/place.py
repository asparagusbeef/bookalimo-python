from __future__ import annotations

from enum import IntEnum
from typing import Optional

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from .common import (
    HEX_COLOR,
    PLACE_ID,
    PLACE_RESOURCE,
    PLACE_TYPE,
    AccessibilityOptions,
    AddressDescriptor,
    Attribution,
    ContentBlock,
    EVChargeOptions,
    FuelOptions,
    LatLng,
    LocalizedText,
    OpeningHours,
    ParkingOptions,
    PaymentOptions,
    Photo,
    PlusCode,
    PostalAddress,
    PriceRange,
    Review,
    SubDestination,
    TimeZone,
    Viewport,
)


class PriceLevel(IntEnum):
    PRICE_LEVEL_UNSPECIFIED = 0
    PRICE_LEVEL_FREE = 1
    PRICE_LEVEL_INEXPENSIVE = 2
    PRICE_LEVEL_MODERATE = 3
    PRICE_LEVEL_EXPENSIVE = 4
    PRICE_LEVEL_VERY_EXPENSIVE = 5


class BusinessStatus(IntEnum):
    BUSINESS_STATUS_UNSPECIFIED = 0
    OPERATIONAL = 1
    CLOSED_TEMPORARILY = 2
    CLOSED_PERMANENTLY = 3


class AddressComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    long_text: str
    short_text: Optional[str] = None
    types: list[str] = Field(
        default_factory=list
    )  # limited to https://developers.google.com/maps/documentation/places/web-service/place-types
    language_code: Optional[str] = None

    @field_validator("types")
    @classmethod
    def _types(cls, v: list[str]) -> list[str]:
        out, seen = [], set()
        for raw in v:
            t = raw.strip()
            if not t:
                raise ValueError("types cannot contain empty strings")
            if not PLACE_TYPE.fullmatch(t):
                raise ValueError(f"invalid place type '{t}'")
            if t not in seen:
                out.append(t)
                seen.add(t)
        return out


class GenerativeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overview: Optional[LocalizedText] = None
    overview_flag_content_uri: Optional[AnyUrl] = None
    disclosure_text: Optional[LocalizedText] = None


class ReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: Optional[LocalizedText] = None
    flag_content_uri: Optional[AnyUrl] = None
    disclosure_text: Optional[LocalizedText] = None


class EvChargeAmenitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overview: ContentBlock
    coffee: Optional[ContentBlock] = None
    restaurant: Optional[ContentBlock] = None
    store: Optional[ContentBlock] = None
    flag_content_uri: Optional[AnyUrl] = None
    disclosure_text: Optional[LocalizedText] = None


class NeighborhoodSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overview: Optional[ContentBlock] = None
    description: Optional[ContentBlock] = None
    flag_content_uri: Optional[AnyUrl] = None
    disclosure_text: Optional[LocalizedText] = None


class ContainingPlace(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str
    id: str

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not PLACE_RESOURCE.fullmatch(v):
            raise ValueError("name must be 'places/{place_id}'")
        return v

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not PLACE_ID.fullmatch(v):
            raise ValueError("id must look like a Place ID")
        return v

    @model_validator(mode="after")
    def _match(self) -> Self:
        if self.name.split("/", 1)[1] != self.id:
            raise ValueError("id must match the trailing component of name")
        return self


class GooglePlace(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    # Identity
    name: Optional[str] = Field(default=None, description="places/{place_id}")
    id: Optional[str] = Field(default=None, description="Place ID")

    # Labels & typing
    display_name: Optional[LocalizedText] = None
    types: list[str] = Field(default_factory=list)
    primary_type: Optional[str] = None
    primary_type_display_name: Optional[LocalizedText] = None

    # Phones & addresses
    national_phone_number: Optional[str] = None
    international_phone_number: Optional[str] = None
    formatted_address: Optional[str] = None
    address_descriptor: Optional[AddressDescriptor] = None
    short_formatted_address: Optional[str] = None
    postal_address: Optional[PostalAddress] = None
    address_components: list[AddressComponent] = Field(default_factory=list)
    plus_code: Optional[PlusCode] = None

    # Location & map
    location: Optional[LatLng] = None
    viewport: Optional[Viewport] = None

    # Scores, links, media
    rating: Optional[float] = None
    google_maps_uri: Optional[AnyUrl] = None
    website_uri: Optional[AnyUrl] = None
    reviews: list[Review] = Field(default_factory=list)
    photos: list[Photo] = Field(default_factory=list)

    # Hours
    regular_opening_hours: Optional[OpeningHours] = None
    current_opening_hours: Optional[OpeningHours] = None
    current_secondary_opening_hours: list[OpeningHours] = Field(default_factory=list)
    regular_secondary_opening_hours: list[OpeningHours] = Field(default_factory=list)
    utc_offset_minutes: Optional[int] = None
    time_zone: Optional[TimeZone] = None

    # Misc attributes
    adr_format_address: Optional[str] = None
    business_status: Optional[BusinessStatus] = None
    price_level: Optional[PriceLevel] = None
    attributions: list[Attribution] = Field(default_factory=list)
    user_rating_count: Optional[int] = None
    icon_mask_base_uri: Optional[AnyUrl] = None
    icon_background_color: Optional[str] = None

    # Food/venue features (optionals in proto)
    takeout: Optional[bool] = None
    delivery: Optional[bool] = None
    dine_in: Optional[bool] = None
    curbside_pickup: Optional[bool] = None
    reservable: Optional[bool] = None
    editorial_summary: Optional[LocalizedText] = None
    serves_breakfast: Optional[bool] = None
    serves_lunch: Optional[bool] = None
    serves_dinner: Optional[bool] = None
    serves_beer: Optional[bool] = None
    serves_wine: Optional[bool] = None
    serves_brunch: Optional[bool] = None
    serves_vegetarian_food: Optional[bool] = None
    outdoor_seating: Optional[bool] = None
    live_music: Optional[bool] = None
    menu_for_children: Optional[bool] = None
    serves_cocktails: Optional[bool] = None
    serves_dessert: Optional[bool] = None
    serves_coffee: Optional[bool] = None
    good_for_children: Optional[bool] = None
    allows_dogs: Optional[bool] = None
    restroom: Optional[bool] = None
    good_for_groups: Optional[bool] = None
    good_for_watching_sports: Optional[bool] = None

    # Options & related places
    payment_options: Optional[PaymentOptions] = None
    parking_options: Optional[ParkingOptions] = None
    sub_destinations: list[SubDestination] = Field(default_factory=list)
    accessibility_options: Optional[AccessibilityOptions] = None

    # Fuel/EV & AI summaries
    fuel_options: Optional[FuelOptions] = None
    ev_charge_options: Optional[EVChargeOptions] = None
    generative_summary: Optional[GenerativeSummary] = None
    review_summary: Optional[ReviewSummary] = None
    ev_charge_amenity_summary: Optional[EvChargeAmenitySummary] = None
    neighborhood_summary: Optional[NeighborhoodSummary] = None

    # Context
    containing_places: list[ContainingPlace] = Field(default_factory=list)
    pure_service_area_business: Optional[bool] = None
    price_range: Optional[PriceRange] = None

    # ---------- Validators ----------
    @field_validator("name")
    @classmethod
    def _name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not PLACE_RESOURCE.fullmatch(v):
            raise ValueError("name must be 'places/{place_id}'")
        return v

    @field_validator("id")
    @classmethod
    def _id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not PLACE_ID.fullmatch(v):
            raise ValueError(
                "id must be a plausible Place ID (base64url-like, >=10 chars)"
            )
        return v

    @model_validator(mode="after")
    def _id_consistency(self) -> Self:
        if self.name and self.id and self.name.split("/", 1)[1] != self.id:
            raise ValueError("id must match trailing component of name")
        return self

    @field_validator("types")
    @classmethod
    def _types(cls, v: list[str]) -> list[str]:
        out, seen = [], set()
        for raw in v:
            t = raw.strip()
            if not t:
                raise ValueError("types cannot contain empty strings")
            if not PLACE_TYPE.fullmatch(t):
                raise ValueError(f"invalid place type '{t}'")
            if t not in seen:
                out.append(t)
                seen.add(t)
        return out

    @model_validator(mode="after")
    def _primary_type_is_in_types(self) -> Self:
        if self.primary_type:
            if not PLACE_TYPE.fullmatch(self.primary_type):
                raise ValueError("primary_type must match place-type token pattern")
            if self.types and self.primary_type not in self.types:
                raise ValueError("primary_type must be included in types")
        return self

    @field_validator("rating")
    @classmethod
    def _rating(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if not (1.0 <= v <= 5.0):
            raise ValueError("rating must be in [1.0, 5.0]")
        return v

    @field_validator("user_rating_count")
    @classmethod
    def _urc(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 0:
            raise ValueError("user_rating_count must be >= 0")
        return v

    @field_validator("icon_background_color")
    @classmethod
    def _hex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not HEX_COLOR.fullmatch(v):
            raise ValueError("icon_background_color must be a hex color like #909CE1")
        return v

    @field_validator("reviews")
    @classmethod
    def _max_reviews(cls, v: list[Review]) -> list[Review]:
        if len(v) > 5:
            raise ValueError("reviews can contain at most 5 items")
        return v

    @field_validator("photos")
    @classmethod
    def _max_photos(cls, v: list[Photo]) -> list[Photo]:
        if len(v) > 10:
            raise ValueError("photos can contain at most 10 items")
        return v
