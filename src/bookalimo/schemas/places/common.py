from __future__ import annotations

import re
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

BCP47 = re.compile(
    r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$"
)  # pragmatic, e.g., "en", "en-US", "zh-Hant"

CLDR_REGION_2 = re.compile(r"^[A-Z]{2}$")  # e.g., "US", "GB"

PLACE_ID = re.compile(
    r"^[A-Za-z0-9_-]{10,}$"
)  # pragmatic: real IDs are long base64url-ish e.g., "ChIJN1t_tDeuEmsRUsoyG83frY4"

PLACE_RESOURCE = re.compile(
    r"^places/[A-Za-z0-9_-]{10,}$"
)  # e.g., "places/ChIJN1t_tDeuEmsRUsoyG83frY4"

PLACE_TYPE = re.compile(r"^[a-z0-9_]+$")  # e.g., "gas_station", "restaurant"

HEX_COLOR = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")  # #abc, #a1b2c3

PLUS_GLOBAL = re.compile(
    r"^[23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]{2,}$"
)  # Open Location Code (Plus Code), pragmatic

BASE64URL_36 = re.compile(
    r"^[A-Za-z0-9_-]{1,36}$"
)  # up to 36 chars, URL-safe base64-ish


# ---------- Fundamental types ----------
class LocalizedText(BaseModel):
    """Localized text with language code."""

    model_config = ConfigDict(extra="allow")

    text: str
    language_code: str

    @field_validator("language_code")
    @classmethod
    def _language_code(cls, v: str) -> str:
        if not BCP47.match(v):
            raise ValueError("language_code must be a valid BCP-47 language tag")
        return v


# ---------- "External" Google message wrappers ----------
class ExternalModel(BaseModel):
    """Permissive wrapper for Google messages we don't model in detail."""

    model_config = ConfigDict(extra="allow")


class OpeningHours(ExternalModel): ...


class PostalAddress(ExternalModel): ...


class TimeZone(ExternalModel): ...


class Timestamp(ExternalModel): ...


class Date(ExternalModel): ...


class ContentBlock(ExternalModel): ...


class Photo(ExternalModel): ...


class Review(ExternalModel): ...


class FuelOptions(ExternalModel): ...


class EVChargeOptions(ExternalModel): ...


class AddressDescriptor(BaseModel):
    """A relational description of a location with nearby landmarks and containing areas."""

    model_config = ConfigDict(extra="forbid")

    class Landmark(BaseModel):
        """Basic landmark information and relationship with target location."""

        model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

        class SpatialRelationship(IntEnum):
            """Spatial relationship between target location and landmark."""

            NEAR = 0
            WITHIN = 1
            BESIDE = 2
            ACROSS_THE_ROAD = 3
            DOWN_THE_ROAD = 4
            AROUND_THE_CORNER = 5
            BEHIND = 6

        name: str = Field(..., description="Landmark's resource name")
        place_id: str = Field(..., description="Landmark's place ID")
        display_name: LocalizedText = Field(..., description="Landmark's display name")
        types: list[str] = Field(
            default_factory=list, description="Type tags for landmark"
        )
        spatial_relationship: SpatialRelationship = Field(
            default=SpatialRelationship.NEAR,
            description="Spatial relationship to target",
        )
        straight_line_distance_meters: float = Field(
            ..., ge=0.0, description="Straight line distance in meters"
        )
        travel_distance_meters: Optional[float] = Field(
            default=None,
            ge=0.0,
            description="Travel distance in meters along road network",
        )

        @field_validator("name")
        @classmethod
        def _name(cls, v: str) -> str:
            if not PLACE_RESOURCE.fullmatch(v):
                raise ValueError("name must be in the form 'places/{place_id}'")
            return v

        @field_validator("place_id")
        @classmethod
        def _place_id(cls, v: str) -> str:
            if not PLACE_ID.fullmatch(v):
                raise ValueError("place_id must be a valid Place ID")
            return v

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
        def _name_id_consistency(self) -> Self:
            if self.name.split("/", 1)[1] != self.place_id:
                raise ValueError("place_id must match the trailing component of name")
            return self

    class Area(BaseModel):
        """Area information and relationship with target location."""

        model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

        class Containment(IntEnum):
            """Spatial relationship between target location and area."""

            CONTAINMENT_UNSPECIFIED = 0
            WITHIN = 1
            OUTSKIRTS = 2
            NEAR = 3

        name: str = Field(..., description="Area's resource name")
        place_id: str = Field(..., description="Area's place ID")
        display_name: LocalizedText = Field(..., description="Area's display name")
        containment: Containment = Field(
            default=Containment.CONTAINMENT_UNSPECIFIED,
            description="Spatial relationship to target",
        )

        @field_validator("name")
        @classmethod
        def _name(cls, v: str) -> str:
            if not PLACE_RESOURCE.fullmatch(v):
                raise ValueError("name must be in the form 'places/{place_id}'")
            return v

        @field_validator("place_id")
        @classmethod
        def _place_id(cls, v: str) -> str:
            if not PLACE_ID.fullmatch(v):
                raise ValueError("place_id must be a valid Place ID")
            return v

        @model_validator(mode="after")
        def _name_id_consistency(self) -> Self:
            if self.name.split("/", 1)[1] != self.place_id:
                raise ValueError("place_id must match the trailing component of name")
            return self

    landmarks: list[Landmark] = Field(
        default_factory=list, description="Ranked list of nearby landmarks"
    )
    areas: list[Area] = Field(
        default_factory=list, description="Ranked list of containing or adjacent areas"
    )

    @field_validator("landmarks")
    @classmethod
    def _max_landmarks(cls, v: list[Landmark]) -> list[Landmark]:
        if len(v) > 10:  # Reasonable limit for API responses
            raise ValueError("landmarks can contain at most 10 items")
        return v

    @field_validator("areas")
    @classmethod
    def _max_areas(cls, v: list[Area]) -> list[Area]:
        if len(v) > 10:  # Reasonable limit for API responses
            raise ValueError("areas can contain at most 10 items")
        return v


class PriceRange(ExternalModel): ...


# ---------- Geometry ----------
class LatLng(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(..., description="[-90, 90]")
    longitude: float = Field(..., description="[-180, 180]")

    @model_validator(mode="after")
    def _check(self) -> Self:
        if not (-90 <= self.latitude <= 90):
            raise ValueError("latitude must be between -90 and 90")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("longitude must be between -180 and 180")
        return self


class Viewport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    high: LatLng
    low: LatLng

    @model_validator(mode="after")
    def _lat_order(self) -> Self:
        if self.high.latitude < self.low.latitude:
            raise ValueError("high.latitude must be >= low.latitude")
        return self


# ---------- Simple shared types ----------
class PlusCode(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    global_code: Optional[str] = Field(default=None, description="e.g., '9FWM33GV+HQ'")
    compound_code: Optional[str] = Field(default=None)

    @field_validator("global_code")
    @classmethod
    def _check_global(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Accept common formats; be permissive.
        if not PLUS_GLOBAL.match(v):
            # Let a variety of valid codes through without being too strict.
            if "+" not in v or len(v) < 6:
                raise ValueError(
                    "global_code must look like a valid plus code (e.g., '9FWM33GV+HQ')."
                )
        return v


class Attribution(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    provider: str
    provider_uri: Optional[AnyUrl] = None


class SubDestination(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., description="places/{place_id}")
    id: str = Field(..., description="{place_id}")

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not PLACE_RESOURCE.fullmatch(v):
            raise ValueError("name must be in the form 'places/{place_id}'")
        return v

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not PLACE_ID.fullmatch(v):
            raise ValueError("id must be a base64url-like token (>=10 chars)")
        return v

    @model_validator(mode="after")
    def _match(self) -> Self:
        if self.name.split("/", 1)[1] != self.id:
            raise ValueError("id must match the trailing component of name")
        return self


class AccessibilityOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wheelchair_accessible_parking: Optional[bool] = None
    wheelchair_accessible_entrance: Optional[bool] = None
    wheelchair_accessible_restroom: Optional[bool] = None
    wheelchair_accessible_seating: Optional[bool] = None


class PaymentOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepts_credit_cards: Optional[bool] = None
    accepts_debit_cards: Optional[bool] = None
    accepts_cash_only: Optional[bool] = None
    accepts_nfc: Optional[bool] = None


class ParkingOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    free_parking_lot: Optional[bool] = None
    paid_parking_lot: Optional[bool] = None
    free_street_parking: Optional[bool] = None
    paid_street_parking: Optional[bool] = None
    valet_parking: Optional[bool] = None
    free_garage_parking: Optional[bool] = None
    paid_garage_parking: Optional[bool] = None
