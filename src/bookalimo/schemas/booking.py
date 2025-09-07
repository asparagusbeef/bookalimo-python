"""
Pydantic schemas for Book-A-Limo booking operations.
Includes all models related to pricing, reservations, and booking requests.
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

from .base import ApiModel


@lru_cache(maxsize=1)
def _load_iata_index() -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Load and index airport data."""
    data = airportsdata.load("IATA")
    by_country: dict[str, list[str]] = {}
    for code, rec in data.items():
        c = (rec.get("country") or "").upper()
        by_country.setdefault(c, []).append(code)
    return data, by_country


class RateType(Enum):
    """Rate types for reservations."""

    P2P = 0  # Point-to-Point (best guess from context)
    HOURLY = 1  # Hourly (best guess from context)
    DAILY = 2  # Daily
    TOUR = 3  # Tour
    ROUND_TRIP = 4  # Round Trip
    RT_HALF = 5  # RT Half


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
    """
    Credit card holder types (API Documentation Unclear).
    TODO: Update when API documentation is clarified by the API author.
    Best guess based on typical credit card processing:
    """

    PERSONAL = 0  # Personal/Individual account (best guess)
    BUSINESS = 1  # Business/Corporate account (best guess)
    # Note: Add UNKNOWN = 3 if you see this value in responses
    UNKNOWN = 3  # From example in API doc


class City(ApiModel):
    """City information."""

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


class Address(ApiModel):
    """
    Address information.
    """

    google_geocode: Optional[dict[str, Any]] = Field(
        default=None, description="Raw Google Geocoding API response (recommended)"
    )
    city: Optional[City] = Field(
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


class Airport(ApiModel):
    """Airport information."""

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
    arriving_from_city: Optional[City] = None
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


class Location(ApiModel):
    """Location (address or airport)."""

    type: LocationType
    address: Optional[Address] = None
    airport: Optional[Airport] = None

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        """Validate that the correct location type is provided."""
        if self.type == LocationType.ADDRESS and not self.address:
            raise ValueError("Address is required when type is ADDRESS")
        if self.type == LocationType.AIRPORT and not self.airport:
            raise ValueError("Airport is required when type is AIRPORT")

        return self


class Stop(ApiModel):
    """Stop information."""

    description: str = Field(..., description="Address, place name, or comment")
    is_en_route: bool = Field(..., description="True if stop is en-route")


class Account(ApiModel):
    """Travel agency or corporate account info."""

    id: str = Field(..., description="TA or corporate account number")
    department: Optional[str] = None
    booker_first_name: Optional[str] = None
    booker_last_name: Optional[str] = None
    booker_email: Optional[str] = None
    booker_phone: Optional[str] = Field(default=None, description="E164 format")


class Passenger(ApiModel):
    """Passenger information."""

    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str = Field(..., description="E164 format recommended")


class Reward(ApiModel):
    """Reward account information."""

    type: RewardType
    value: str = Field(..., description="Reward account number")


class CreditCard(ApiModel):
    """Credit card information."""

    number: str
    expiration: str = Field(..., description="MM/YY format")
    cvv: str
    card_holder: str
    zip: Optional[str] = None
    holder_type: Optional[CardHolderType] = Field(
        default=None,
        description="Card holder type - API documentation unclear, using best guess",
    )


class BreakdownItem(ApiModel):
    """Price breakdown item."""

    name: str
    value: float
    is_grand: bool = Field(
        ..., description="True if item should be highlighted (totals)"
    )


class MeetGreetAdditional(ApiModel):
    """Additional meet & greet charges."""

    name: str
    price: float


class MeetGreet(ApiModel):
    """Meet & greet option."""

    id: int
    name: str
    base_price: float
    instructions: str
    additional: list[MeetGreetAdditional]
    total_price: float
    fees: float
    reservation_price: float


class Price(ApiModel):
    """Car class pricing information."""

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
    meet_greets: list[MeetGreet] = Field(default_factory=list)


class Reservation(ApiModel):
    """Basic reservation information."""

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


class EditableReservationRequest(ApiModel):
    """
    Editable reservation for modifications.

    Note: API documentation inconsistency - credit_card marked as required in model
    but omitted in edit examples. Making it optional as edit requests may not need it.
    TODO: Clarify with API author when credit_card is actually required.
    """

    confirmation: str
    is_cancel_request: bool = False
    rate_type: Optional[RateType] = None
    pickup_date: Optional[str] = Field(default=None, description="MM/dd/yyyy format")
    pickup_time: Optional[str] = Field(default=None, description="hh:mm tt format")
    stops: Optional[list[Stop]] = None
    credit_card: Optional[CreditCard] = Field(
        default=None,
        description="Conditionally required - unclear from API docs when exactly",
    )
    passengers: Optional[int] = None
    luggage: Optional[int] = None
    pets: Optional[int] = None
    car_seats: Optional[int] = None
    boosters: Optional[int] = None
    infants: Optional[int] = None
    other: Optional[str] = Field(default=None, description="Other changes not listed")


# Request/Response Models


class PriceRequest(ApiModel):
    """Request for getting prices."""

    rate_type: RateType
    date_time: str = Field(..., description="MM/dd/yyyy hh:mm tt format")
    pickup: Location
    dropoff: Location
    hours: Optional[int] = Field(default=None, description="For hourly rate_type only")
    passengers: int
    luggage: int
    stops: Optional[list[Stop]] = None
    account: Optional[Account] = Field(
        default=None, description="TAs must provide for commission"
    )
    passenger: Optional[Passenger] = None
    rewards: Optional[list[Reward]] = None
    car_class_code: Optional[str] = Field(
        default=None, description="e.g., 'SD' for specific car class"
    )
    pets: Optional[int] = None
    car_seats: Optional[int] = None
    boosters: Optional[int] = None
    infants: Optional[int] = None
    customer_comment: Optional[str] = None


class PriceResponse(ApiModel):
    """Response from get prices."""

    token: str
    prices: list[Price]


class DetailsRequest(ApiModel):
    """Request for setting reservation details."""

    token: str
    car_class_code: Optional[str] = None
    pickup: Optional[Location] = None
    dropoff: Optional[Location] = None
    stops: Optional[list[Stop]] = None
    account: Optional[Account] = None
    passenger: Optional[Passenger] = None
    rewards: Optional[list[Reward]] = None
    pets: Optional[int] = None
    car_seats: Optional[int] = None
    boosters: Optional[int] = None
    infants: Optional[int] = None
    customer_comment: Optional[str] = None
    ta_fee: Optional[float] = Field(
        default=None, description="For Travel Agencies - additional fee in USD"
    )


class DetailsResponse(ApiModel):
    """Response from set details."""

    price: float
    breakdown: list[BreakdownItem]


class BookRequest(ApiModel):
    """Request for booking reservation."""

    token: str
    promo: Optional[str] = None
    method: Optional[str] = Field(
        default=None, description="'charge' for charge accounts"
    )
    credit_card: Optional[CreditCard] = None

    @model_validator(mode="after")
    def validate_book_request(self) -> Self:
        """Validate that either method or credit_card is provided."""
        if not self.method and not self.credit_card:
            raise ValueError("Either method='charge' or credit_card must be provided")

        return self


class BookResponse(ApiModel):
    """Response from book reservation."""

    reservation_id: str


class ListReservationsRequest(ApiModel):
    """Request for listing reservations."""

    is_archive: bool = False


class ListReservationsResponse(ApiModel):
    """Response from list reservations."""

    success: bool
    reservations: list[Reservation] = Field(default_factory=list)
    error: Optional[str] = None


class GetReservationRequest(ApiModel):
    """Request for getting reservation details."""

    confirmation: str


class GetReservationResponse(ApiModel):
    """Response from get reservation."""

    reservation: EditableReservationRequest
    is_editable: bool
    status: Optional[ReservationStatus] = None
    is_cancellation_pending: bool
    car_description: Optional[str] = None
    cancellation_policy: Optional[str] = None
    pickup_type: LocationType
    pickup_description: str
    dropoff_type: LocationType
    dropoff_description: str
    additional_services: Optional[str] = None
    payment_method: Optional[str] = None
    breakdown: list[BreakdownItem] = Field(default_factory=list)
    passenger_name: Optional[str] = None
    evoucher_url: Optional[str] = None
    receipt_url: Optional[str] = None
    pending_changes: list[list[str]] = Field(default_factory=list)


class EditReservationResponse(ApiModel):
    """Response from edit reservation."""

    success: bool
