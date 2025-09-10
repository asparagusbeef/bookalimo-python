"""
Shared base models for Book-A-Limo API data structures.
Contains field definitions without serialization opinions -
request/response variants inherit from these and set appropriate serialization.
"""

import warnings
from enum import Enum
from functools import lru_cache
from typing import Any, Optional

import airportsdata
import pycountry
import us
from pydantic import Field, model_validator
from typing_extensions import Self

from .base import SharedModel


@lru_cache(maxsize=1)
def _load_iata_index() -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Load and index airport data."""
    data = airportsdata.load("IATA")
    by_country: dict[str, list[str]] = {}
    for code, rec in data.items():
        c = (rec.get("country") or "").upper()
        by_country.setdefault(c, []).append(code)
    return data, by_country


# Enums (no serialization issues)
class RateType(Enum):
    """Rate types for reservations."""

    P2P = 0  # Point-to-Point
    HOURLY = 1  # Hourly
    DAILY = 2  # Daily
    TOUR = 3  # Tour
    ROUND_TRIP = 4  # Round Trip
    RT_HALF = 5  # Round Trip Half Day


class LocationType(Enum):
    """Location types."""

    ADDRESS = 0
    AIRPORT = 1
    TRAIN_STATION = 2
    CRUISE = 3


class MeetGreetType(Enum):
    """Meet & Greet options."""

    OTHER = 0
    FBO = 1
    BAGGAGE_CLAIM = 2
    CURB_SIDE = 3
    GATE = 4
    INTERNATIONAL = 5
    GREETER_SERVICE = 6


class RewardType(Enum):
    """Reward account types."""

    UNITED_MILEAGEPLUS = 0


class ReservationStatus(Enum):
    """Reservation status."""

    ACTIVE = None
    NO_SHOW = 0
    CANCELED = 1
    LATE_CANCELED = 2


class CardHolderType(Enum):
    """Credit card holder types."""

    CORPORATE = 0
    AGENCY = 1
    THIRD_PARTY = 2
    SAME_AS_PASSENGER = 3


# Shared Data Models
class CityBase(SharedModel):
    """Base city information."""

    city_name: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    state_code: Optional[str] = Field(default=None, description="US state code")
    state_name: Optional[str] = Field(default=None, description="US state name")

    @model_validator(mode="after")
    def validate_country_code(self) -> Self:
        """Validate that country_code is a valid ISO 3166-1 alpha-2 country code."""
        if not pycountry.countries.get(alpha_2=self.country_code):
            raise ValueError(f"Invalid country code: {self.country_code}")

        return self

    @model_validator(mode="after")
    def validate_us(self) -> Self:
        """Validate that state_code is a valid US state code and state_name is a valid US state name."""
        if self.country_code != "US":
            return self

        code_match = us.states.lookup(str(self.state_code))
        name_match = us.states.lookup(str(self.state_name))
        if not code_match and not name_match:
            raise ValueError(
                f"Invalid state code or name: {self.state_code} or {self.state_name}"
            )
        if code_match and name_match and code_match != name_match:
            raise ValueError(
                f"State code and name do not match: {self.state_code} and {self.state_name}"
            )
        match = code_match or name_match
        if match:
            self.state_code = match.abbr
            self.state_name = match.name
            return self
        raise ValueError(
            f"Invalid state code or name: {self.state_code} or {self.state_name}"
        )


class AddressBase(SharedModel):
    """Base address information."""

    google_geocode: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Raw Google Geocoding API result (recommended). "
            "Common mistake is to use the response object instead of the result object. "
            "You must use geocode_response['results'][0] to get the result object."
        ),
    )
    city: Optional["CityBase"] = Field(
        default=None, description="Use only if google_geocode not available"
    )
    district: Optional[str] = Field(default=None, description="e.g., Manhattan")
    neighbourhood: Optional[str] = Field(
        default=None, description="e.g., Lower Manhattan"
    )
    place_name: Optional[str] = Field(
        default=None, description="e.g., Empire State Building"
    )
    street_name: Optional[str] = Field(default=None, description="e.g., East 34th St")
    building: Optional[str] = Field(default=None, description="e.g., 53")
    suite: Optional[str] = Field(default=None, description="e.g., 5P")
    zip: Optional[str] = Field(default=None, description="e.g., 10016")

    @model_validator(mode="after")
    def validate_address(self) -> Self:
        """Validate that either place_name or street_name is provided."""
        if not self.place_name and not self.street_name:
            raise ValueError("Either place_name or street_name must be provided")

        return self

    @model_validator(mode="after")
    def validate_city_or_google_geocode(self) -> Self:
        """Validate that exactly one of city or google_geocode is provided, with preference for google_geocode."""
        if not self.city and not self.google_geocode:
            raise ValueError("Either city or google_geocode must be provided")

        if self.city and self.google_geocode:
            raise ValueError("Only one of city or google_geocode must be provided")

        if self.city:
            warnings.warn(
                "Using google_geocode instead of city is recommended.",
                stacklevel=3,
            )

        return self


class AirportBase(SharedModel):
    """Base airport information."""

    iata_code: str = Field(..., description="3-letter IATA code, e.g., JFK")
    country_code: Optional[str] = Field(default=None, description="ISO 3166-1 alpha-2")
    state_code: Optional[str] = Field(
        default=None, description="US state code, e.g., NY"
    )
    airline_iata_code: Optional[str] = Field(
        default=None, description="2-letter IATA airline code"
    )
    airline_icao_code: Optional[str] = Field(
        default=None, description="3-letter ICAO airline code"
    )
    flight_number: Optional[str] = Field(default=None, description="e.g., UA1234")
    terminal: Optional[str] = Field(default=None, description="e.g., 7")
    arriving_from_city: Optional["CityBase"] = None
    meet_greet: Optional[int] = Field(
        default=None,
        description="Meet & greet option ID. Leave empty on price request to see options.",
    )

    @model_validator(mode="after")
    def validate_country_code(self) -> Self:
        """Validate that country_code is a valid ISO 3166-1 alpha-2 country code."""
        if self.country_code and not pycountry.countries.get(alpha_2=self.country_code):
            raise ValueError(f"Invalid country code: {self.country_code}")

        return self

    @model_validator(mode="after")
    def validate_state_code(self) -> Self:
        """Validate that state_code is a valid US state code."""
        if self.state_code and not us.states.lookup(str(self.state_code)):
            raise ValueError(f"Invalid state code: {self.state_code}")

        return self

    @model_validator(mode="after")
    def validate_airport(self) -> Self:
        """Validate that iata_code is a valid IATA code."""
        if self.iata_code not in _load_iata_index()[0]:
            raise ValueError(f"Invalid IATA code: {self.iata_code}")

        return self


class LocationBase(SharedModel):
    """Base location (address or airport)."""

    type: LocationType
    address: Optional["AddressBase"] = None
    airport: Optional["AirportBase"] = None

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        """Validate that the correct location type is provided."""
        if self.type == LocationType.ADDRESS and not self.address:
            raise ValueError("Address is required when type is ADDRESS")
        if self.type == LocationType.AIRPORT and not self.airport:
            raise ValueError("Airport is required when type is AIRPORT")

        return self


class StopBase(SharedModel):
    """Base stop information."""

    description: str = Field(..., description="Address, place name, or comment")
    is_en_route: bool = Field(..., description="True if stop is en-route")


class AccountBase(SharedModel):
    """Base travel agency or corporate account info."""

    id: str = Field(..., description="TA or corporate account number")
    department: Optional[str] = None
    booker_first_name: Optional[str] = None
    booker_last_name: Optional[str] = None
    booker_email: Optional[str] = None
    booker_phone: Optional[str] = Field(default=None, description="E164 format")


class PassengerBase(SharedModel):
    """Base passenger information."""

    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str = Field(..., description="E164 format recommended")


class RewardBase(SharedModel):
    """Base reward account information."""

    type: RewardType
    value: str = Field(..., description="Reward account number")


class CreditCardBase(SharedModel):
    """Base credit card information."""

    number: str
    expiration: str = Field(..., description="MM/YY format")
    cvv: str
    card_holder: str
    zip: Optional[str] = None
    holder_type: Optional[CardHolderType] = Field(
        default=None,
        description="Card holder type",
    )


class BreakdownItemBase(SharedModel):
    """Base price breakdown item."""

    name: str
    value: float
    is_grand: bool = Field(
        ..., description="True if item should be highlighted (totals)"
    )


class MeetGreetAdditionalBase(SharedModel):
    """Base additional meet & greet charges."""

    name: str
    price: float


class MeetGreetBase(SharedModel):
    """Base meet & greet option."""

    id: int
    name: str
    base_price: float
    instructions: str
    additional: list["MeetGreetAdditionalBase"]
    total_price: float
    fees: float
    reservation_price: float


class PriceBase(SharedModel):
    """Base car class pricing information."""

    car_class: str
    car_description: str
    max_passengers: int
    max_luggage: int
    price: float = Field(..., description="Price WITHOUT Meet&Greet")
    price_default: float = Field(..., description="Price WITH default Meet&Greet")
    image_128: str = Field(alias="image128")
    image_256: str = Field(alias="image256")
    image_512: str = Field(alias="image512")
    default_meet_greet: Optional[int] = None
    meet_greets: list["MeetGreetBase"] = Field(default_factory=list)


class ReservationBase(SharedModel):
    """Base reservation information."""

    confirmation_number: str
    is_archive: bool
    local_date_time: str
    eastern_date_time: Optional[str] = None
    rate_type: RateType
    passenger_name: Optional[str] = None
    pickup_type: LocationType
    pickup: str
    dropoff_type: LocationType
    dropoff: str
    car_class: str
    status: Optional[ReservationStatus] = None
