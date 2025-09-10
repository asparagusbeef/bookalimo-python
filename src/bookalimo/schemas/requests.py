"""
Request models for Book-A-Limo API operations.
These models serialize to camelCase by default for API compatibility.
"""

from typing import Optional

from pydantic import Field, model_validator
from typing_extensions import Self

from .base import RequestModel
from .shared import (
    AccountBase,
    AddressBase,
    AirportBase,
    BreakdownItemBase,
    CityBase,
    CreditCardBase,
    LocationBase,
    MeetGreetAdditionalBase,
    MeetGreetBase,
    PassengerBase,
    PriceBase,
    RateType,
    ReservationBase,
    RewardBase,
    StopBase,
)


# Request versions of shared models (serialize to camelCase)
class City(CityBase, RequestModel):
    """City information for requests."""

    pass


class Address(AddressBase, RequestModel):
    """Address information for requests."""

    city: Optional[City] = Field(
        default=None, description="Use only if google_geocode not available"
    )


class Airport(AirportBase, RequestModel):
    """Airport information for requests."""

    arriving_from_city: Optional[City] = None


class Location(LocationBase, RequestModel):
    """Location (address or airport) for requests."""

    address: Optional[Address] = None
    airport: Optional[Airport] = None


class Stop(StopBase, RequestModel):
    """Stop information for requests."""

    pass


class Account(AccountBase, RequestModel):
    """Travel agency or corporate account info for requests."""

    pass


class Passenger(PassengerBase, RequestModel):
    """Passenger information for requests."""

    pass


class Reward(RewardBase, RequestModel):
    """Reward account information for requests."""

    pass


class CreditCard(CreditCardBase, RequestModel):
    """Credit card information for requests."""

    pass


class BreakdownItem(BreakdownItemBase, RequestModel):
    """Price breakdown item for requests."""

    pass


class MeetGreetAdditional(MeetGreetAdditionalBase, RequestModel):
    """Additional meet & greet charges for requests."""

    pass


class MeetGreet(MeetGreetBase, RequestModel):
    """Meet & greet option for requests."""

    pass


class Price(PriceBase, RequestModel):
    """Car class pricing information for requests."""

    pass


class Reservation(ReservationBase, RequestModel):
    """Basic reservation information for requests."""

    pass


class EditReservationRequest(RequestModel):
    """Editable reservation for modifications (requests)."""

    confirmation: str
    is_cancel_request: bool = False
    rate_type: Optional[RateType] = None
    pickup_date: Optional[str] = Field(default=None, description="MM/dd/yyyy format")
    pickup_time: Optional[str] = Field(default=None, description="hh:mm tt format")
    stops: Optional[list[Stop]] = None
    credit_card: Optional[CreditCard] = None
    passengers: Optional[int] = None
    luggage: Optional[int] = None
    pets: Optional[int] = None
    car_seats: Optional[int] = None
    boosters: Optional[int] = None
    infants: Optional[int] = None
    other: Optional[str] = Field(default=None, description="Other changes not listed")


# Pure Request Models
class PriceRequest(RequestModel):
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


class DetailsRequest(RequestModel):
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


class BookRequest(RequestModel):
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


class ListReservationsRequest(RequestModel):
    """Request for listing reservations."""

    is_archive: bool = False


class GetReservationRequest(RequestModel):
    """Request for getting reservation details."""

    confirmation: str
