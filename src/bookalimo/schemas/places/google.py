import re
from typing import Any, Optional, cast

import pycountry
from httpx import QueryParams
from pycountry.db import Country
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from .common import (
    BASE64URL_36,
    BCP47,
    CLDR_REGION_2,
    PLACE_ID,
    PLACE_RESOURCE,
    PLACE_TYPE,
    LatLng,
    Viewport,
)
from .place import Place as GooglePlace

# ---------- Constants & Enums ----------

COUNTRY_CODES = {
    country.alpha_2 for country in cast(list[Country], list(pycountry.countries))
}


class PlaceType:
    """Place type constants."""

    ADDRESS = "address"
    AIRPORT = "airport"
    POI = "poi"  # Point of Interest


# ---------- Text Primitives ----------
class StringRange(BaseModel):
    """Identifies a substring within a given text."""

    model_config = ConfigDict(extra="forbid")

    start_offset: int = Field(
        default=0, ge=0, description="Zero-based start (inclusive)"
    )
    end_offset: int = Field(..., ge=0, description="Zero-based end (exclusive)")

    @model_validator(mode="after")
    def _validate_order(self) -> Self:
        if self.start_offset >= self.end_offset:
            raise ValueError("start_offset must be < end_offset")
        return self


class FormattableText(BaseModel):
    """Text that can be highlighted via `matches` ranges."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(..., min_length=1)
    matches: list[StringRange] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_matches(self) -> Self:
        n = len(self.text)
        prev_end = -1
        for i, r in enumerate(self.matches):
            if r.end_offset > n:
                raise ValueError(f"matches[{i}] end_offset exceeds text length ({n})")
            if r.start_offset < 0:
                raise ValueError(f"matches[{i}] start_offset must be >= 0")
            # Enforce strictly increasing, non-overlapping ranges (stronger than spec but safe)
            if r.start_offset <= prev_end:
                raise ValueError(
                    "matches must be ordered by increasing, non-overlapping offsets"
                )
            prev_end = r.end_offset
        return self


class StructuredFormat(BaseModel):
    """Breakdown of a prediction into main and secondary text."""

    model_config = ConfigDict(extra="forbid")

    main_text: FormattableText
    secondary_text: FormattableText


# ---------- Geometry Primitives ----------


class Circle(BaseModel):
    """google.maps.places_v1.types.Circle (center + radius)."""

    model_config = ConfigDict(extra="forbid")

    center: LatLng
    radius_meters: float = Field(
        ..., gt=0, description="Strictly positive radius in meters"
    )


class LocationBias(BaseModel):
    """
    Oneof: exactly one of rectangle or circle must be set.
    """

    model_config = ConfigDict(extra="forbid")

    rectangle: Optional[Viewport] = None
    circle: Optional[Circle] = None

    @model_validator(mode="after")
    def _validate_oneof(self) -> Self:
        set_count = sum(x is not None for x in (self.rectangle, self.circle))
        if set_count != 1:
            raise ValueError(
                "Exactly one of {rectangle, circle} must be set for LocationBias"
            )
        return self


class LocationRestriction(BaseModel):
    """
    Oneof: exactly one of rectangle or circle must be set.
    """

    model_config = ConfigDict(extra="forbid")

    rectangle: Optional[Viewport] = None
    circle: Optional[Circle] = None

    @model_validator(mode="after")
    def _validate_oneof(self) -> Self:
        set_count = sum(x is not None for x in (self.rectangle, self.circle))
        if set_count != 1:
            raise ValueError(
                "Exactly one of {rectangle, circle} must be set for LocationRestriction"
            )
        return self


# ---------- Responses ----------


class Place(BaseModel):
    """Structured place result from the Google Places API."""

    formatted_address: str = Field(..., description="Full formatted address")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    place_type: str = Field(..., description="Type: address, airport, or poi")
    iata_code: Optional[str] = Field(
        None, description="IATA airport code if applicable"
    )
    google_place: Optional[GooglePlace] = Field(
        None, description="Raw Google Places API response"
    )

    @computed_field
    @property
    def country_code(self) -> Optional[str]:
        """Return ISO 3166-1 alpha-2 country code from the Google Places API response."""
        return self.extract_country_alpha2(self.google_place)

    @model_validator(mode="after")
    def validate_place_type(self) -> Self:
        """Validate place_type is one of the allowed values."""
        if self.place_type not in [PlaceType.ADDRESS, PlaceType.AIRPORT, PlaceType.POI]:
            raise ValueError(f"Invalid place_type: {self.place_type}")
        return self

    @staticmethod
    def extract_country_alpha2(google_place: Optional[GooglePlace]) -> Optional[str]:
        """Return ISO 3166-1 alpha-2 country code from a Google Places result."""
        if not google_place:
            return None

        for comp in google_place.address_components:
            if "country" in comp.types:
                code = (comp.short_text or "").upper()
                return code if code in COUNTRY_CODES and len(code) == 2 else None
        return None


class AutocompletePlacesResponse(BaseModel):
    """Response proto for AutocompletePlaces: ordered suggestions."""

    model_config = ConfigDict(extra="forbid")

    suggestions: list["Suggestion"] = Field(default_factory=list)


class PlacePrediction(BaseModel):
    """Prediction result representing a Place."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    place: str = Field(..., description="Resource name, e.g., 'places/PLACE_ID'")
    place_id: str = Field(..., description="Place ID string")
    text: Optional[FormattableText] = None
    structured_format: Optional[StructuredFormat] = None
    types: list[str] = Field(default_factory=list, description="Place types")
    distance_meters: Optional[int] = Field(default=None, ge=0)

    @field_validator("place")
    @classmethod
    def _valid_place_resource(cls, v: str) -> str:
        if not PLACE_RESOURCE.fullmatch(v):
            raise ValueError("place must match ^places/[A-Za-z0-9_-]{3,}$")
        return v

    @field_validator("place_id")
    @classmethod
    def _valid_place_id(cls, v: str) -> str:
        if not PLACE_ID.fullmatch(v):
            raise ValueError("place_id must be a base64url-like token of length >= 10")
        return v

    @field_validator("types")
    @classmethod
    def _validate_types(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen = set()
        for raw in v:
            t = raw.strip()
            if not t:
                raise ValueError("types cannot contain empty strings")
            if not PLACE_TYPE.fullmatch(t):
                raise ValueError(
                    f"Invalid place type '{t}'. Use lowercase letters, digits, and underscores."
                )
            if t not in seen:
                cleaned.append(t)
                seen.add(t)
        return cleaned

    @model_validator(mode="after")
    def _at_least_one_text_representation(self) -> Self:
        if self.text is None and self.structured_format is None:
            raise ValueError(
                "At least one of {text, structured_format} must be provided"
            )
        return self


class QueryPrediction(BaseModel):
    """Prediction result representing a query (not a Place)."""

    model_config = ConfigDict(extra="forbid")

    text: Optional[FormattableText] = None
    structured_format: Optional[StructuredFormat] = None

    @model_validator(mode="after")
    def _at_least_one_text_representation(self) -> Self:
        if self.text is None and self.structured_format is None:
            raise ValueError(
                "At least one of {text, structured_format} must be provided"
            )
        return self


class Suggestion(BaseModel):
    """
    Oneof 'kind': exactly one of place_prediction or query_prediction must be set.
    """

    model_config = ConfigDict(extra="forbid")

    place_prediction: Optional[PlacePrediction] = None
    query_prediction: Optional[QueryPrediction] = None

    @model_validator(mode="after")
    def _validate_oneof(self) -> Self:
        count = sum(
            x is not None for x in (self.place_prediction, self.query_prediction)
        )
        if count != 1:
            raise ValueError(
                "Exactly one of {place_prediction, query_prediction} must be set"
            )
        return self


# ---------- Requests ----------


class GetPlaceRequest(BaseModel):
    """
    Request for fetching a Place by resource name 'places/{place_id}'.

    - name: required, must match ^places/[A-Za-z0-9_-]{10,}$
    - language_code: optional BCP-47 tag (e.g., 'en', 'en-US', 'zh-Hant')
    - region_code: optional CLDR region code (2 letters, uppercase). 3-digit codes not supported.
    - session_token: optional base64url (URL/filename-safe) up to 36 chars.
    """

    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, populate_by_name=True
    )

    name: str = Field(..., description="Resource name in the form 'places/{place_id}'.")
    language_code: Optional[str] = Field(
        default=None,
        description="Preferred language (BCP-47). If unavailable, backend defaults apply.",
    )
    region_code: Optional[str] = Field(
        default=None,
        description="CLDR region code (2 letters, e.g., 'US'). 3-digit codes not supported.",
    )
    session_token: Optional[str] = Field(
        default=None,
        description="Base64url token (URL/filename-safe), length 1–36, for Autocomplete billing sessions.",
    )

    # ---- Field validators ----
    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not PLACE_RESOURCE.fullmatch(v):
            raise ValueError(
                "name must be in the form 'places/{place_id}' with a base64url-like place_id (>=10 chars)."
            )
        return v

    @field_validator("language_code")
    @classmethod
    def _validate_language_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not BCP47.match(v):
            raise ValueError(
                "language_code must be a valid BCP-47 tag (e.g., 'en', 'en-US', 'zh-Hant')."
            )
        return v

    @field_validator("region_code")
    @classmethod
    def _validate_region_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v2 = v.upper()
        if not CLDR_REGION_2.fullmatch(v2):
            raise ValueError(
                "region_code must be a two-letter CLDR region code (e.g., 'US', 'GB')."
            )
        return v2

    @field_validator("session_token")
    @classmethod
    def _validate_session_token(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not BASE64URL_36.fullmatch(v):
            raise ValueError(
                "session_token must be base64url (A–Z a–z 0–9 _ -), length 1–36."
            )
        return v

    # ---- Convenience (not part of the wire schema) ----
    @property
    def place_id(self) -> str:
        """Extract the {place_id} from 'places/{place_id}'."""
        return self.name.split("/", 1)[1]


class AutocompletePlacesRequest(BaseModel):
    """
    Pydantic v2 model for AutocompletePlacesRequest with rich validations.
    """

    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, populate_by_name=True
    )

    # Required search text
    input: str = Field(
        ..., min_length=1, description="The text string on which to search."
    )

    # Mutually exclusive geospatial hints (top-level 'at most one' rule)
    location_bias: Optional[LocationBias] = None
    location_restriction: Optional[LocationRestriction] = None

    # Place types (<= 5). Either a list of normal types OR exactly one of the special tokens.
    included_primary_types: list[str] = Field(default_factory=list)

    # Region filters (<= 15) as CLDR two-letter codes (uppercased, de-duplicated).
    included_region_codes: list[str] = Field(default_factory=list)

    # Localization
    language_code: str = Field(
        default="en-US", description="BCP-47 language tag, default en-US."
    )
    region_code: Optional[str] = Field(
        default=None, description="CLDR region code (2 letters, e.g., 'US')."
    )

    # Distance origin (if present, distance is returned)
    origin: Optional[LatLng] = None

    # Cursor position in `input`; if omitted, defaults to len(input)
    input_offset: Optional[int] = None

    # Flags
    include_query_predictions: bool = False
    include_pure_service_area_businesses: bool = False

    # Session token: URL/filename safe base64url, <= 36 ASCII chars
    session_token: Optional[str] = None

    # -------------------- Field-level validations & normalization --------------------

    @field_validator("included_primary_types")
    @classmethod
    def _validate_primary_types(cls, v: list[str]) -> list[str]:
        # Enforce <= 5, no empties, trim & dedupe (preserving order)
        if len(v) > 5:
            raise ValueError("included_primary_types can contain at most 5 values")
        cleaned: list[str] = []
        seen = set()
        for raw in v:
            t = raw.strip()
            if not t:
                raise ValueError("included_primary_types cannot contain empty strings")
            if t not in seen:
                cleaned.append(t)
                seen.add(t)

        # Special tokens constraint: allow exactly one item when using "(regions)" or "(cities)"
        specials = {"(regions)", "(cities)"}
        if any(t in specials for t in cleaned):
            if len(cleaned) != 1 or cleaned[0] not in specials:
                raise ValueError(
                    "When using special tokens, included_primary_types must be exactly one of '(regions)' or '(cities)'."
                )
            return cleaned

        # Otherwise validate normal place-type tokens format (lowercase, digits, underscores)
        for t in cleaned:
            if not PLACE_TYPE.match(t):
                raise ValueError(
                    f"Invalid place type '{t}'. Use lowercase letters, digits, and underscores (e.g., 'gas_station')."
                )
        return cleaned

    @field_validator("included_region_codes")
    @classmethod
    def _validate_region_codes(cls, v: list[str]) -> list[str]:
        if len(v) > 15:
            raise ValueError("included_region_codes can contain at most 15 values")
        out: list[str] = []
        seen = set()
        for raw in v:
            code = raw.strip().upper()
            if not re.fullmatch(r"[A-Z]{2}", code):
                raise ValueError(
                    f"Region code '{raw}' must be a two-letter CLDR region code (e.g., 'US', 'GB')."
                )
            if code not in seen:
                out.append(code)
                seen.add(code)
        return out

    @field_validator("language_code")
    @classmethod
    def _validate_language_code(cls, v: str) -> str:
        if not BCP47.match(v):
            raise ValueError(
                "language_code must be a valid BCP-47 tag (e.g., 'en', 'en-US', 'zh-Hant')."
            )
        return v

    @field_validator("region_code")
    @classmethod
    def _validate_region_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v2 = v.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", v2):
            raise ValueError(
                "region_code must be a two-letter CLDR region code (e.g., 'US', 'GB')."
            )
        return v2

    @field_validator("session_token")
    @classmethod
    def _validate_session_token(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # URL/filename-safe base64 (base64url) up to 36 chars: A–Z a–z 0–9 _ -
        if not BASE64URL_36.fullmatch(v):
            raise ValueError(
                "session_token must be URL/filename-safe base64 (base64url) of length 1–36 using [A-Za-z0-9_-]."
            )
        return v

    @field_validator("input")
    @classmethod
    def _validate_input_nonempty(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("input cannot be empty")
        return v

    @field_validator("input_offset")
    @classmethod
    def _validate_input_offset(cls, v: Optional[int], info: Any) -> Optional[int]:
        # Can't compare to input length here (other fields not guaranteed yet),
        # so we only enforce non-negative. Range is finished in the model_validator below.
        if v is not None and v < 0:
            raise ValueError("input_offset must be a non-negative integer")
        return v

    # -------------------- Cross-field validations --------------------

    @model_validator(mode="after")
    def _validate_cross_fields(self) -> Self:
        # Top-level exclusivity: at most one of location_bias / location_restriction
        if self.location_bias is not None and self.location_restriction is not None:
            raise ValueError(
                "At most one of {location_bias, location_restriction} may be set."
            )

        # Default input_offset to len(input) if omitted; else enforce range
        if self.input_offset is None:
            object.__setattr__(self, "input_offset", len(self.input))
        else:
            if self.input_offset > len(self.input):
                raise ValueError(
                    "input_offset cannot be greater than the length of input"
                )

        return self


class GeocodingRequest(BaseModel):
    """
    Pydantic model for validating and building Geocoding API query parameters.
    This model is not for a JSON request body, but for constructing a URL.
    """

    address: Optional[str] = Field(
        default=None,
        description="The street address or plus code that you want to geocode.",
    )
    place_id: Optional[str] = Field(
        default=None,
        description="The place ID of the place for which you wish to obtain the human-readable address.",
    )
    language: Optional[str] = Field(
        default=None, description="The language in which to return results."
    )
    region: Optional[str] = Field(
        default=None, description="The region code (ccTLD) to bias results."
    )

    @model_validator(mode="before")
    @classmethod
    def check_required_params(cls, data: Any) -> Any:
        """Ensures that either 'address', 'place_id', or 'components' is provided."""
        if isinstance(data, dict):
            if not any(
                [data.get("address"), data.get("place_id"), data.get("components")]
            ):
                raise ValueError(
                    "You must specify either 'address', 'place_id', or 'components'."
                )
        return data

    def to_query_params(self) -> QueryParams:
        """
        Serializes the model fields into a dictionary suitable for URL query parameters.
        """
        params = QueryParams()
        if self.address:
            params = params.add("address", self.address)

        if self.place_id:
            params = params.add("place_id", self.place_id)

        if self.language:
            params = params.add("language", self.language)

        if self.region:
            params = params.add("region", self.region)

        return params
