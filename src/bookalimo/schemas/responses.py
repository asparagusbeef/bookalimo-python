"""
Response models for Book-A-Limo API operations.
These models serialize to snake_case by default for better Python DX.
"""

from typing import Optional

from pydantic import Field

from .base import ResponseModel
from .shared import (
    AccountBase,
    AddressBase,
    AirportBase,
    BreakdownItemBase,
    CityBase,
    CreditCardBase,
    LocationBase,
    LocationType,
    MeetGreetAdditionalBase,
    MeetGreetBase,
    PassengerBase,
    PriceBase,
    RateType,
    ReservationBase,
    ReservationStatus,
    RewardBase,
    StopBase,
)


# Response versions of shared models (serialize to snake_case)
class City(CityBase, ResponseModel):
    """City information for responses."""

    pass


class Address(AddressBase, ResponseModel):
    """Address information for responses."""

    city: Optional[City] = Field(
        default=None, description="Use only if google_geocode not available"
    )


class Airport(AirportBase, ResponseModel):
    """Airport information for responses."""

    arriving_from_city: Optional[City] = None


class Location(LocationBase, ResponseModel):
    """Location (address or airport) for responses."""

    address: Optional[Address] = None
    airport: Optional[Airport] = None


class Stop(StopBase, ResponseModel):
    """Stop information for responses."""

    pass


class Account(AccountBase, ResponseModel):
    """Travel agency or corporate account info for responses."""

    pass


class Passenger(PassengerBase, ResponseModel):
    """Passenger information for responses."""

    pass


class Reward(RewardBase, ResponseModel):
    """Reward account information for responses."""

    pass


class CreditCard(CreditCardBase, ResponseModel):
    """Credit card information for responses."""

    pass


class BreakdownItem(BreakdownItemBase, ResponseModel):
    """Price breakdown item for responses."""

    pass


class MeetGreetAdditional(MeetGreetAdditionalBase, ResponseModel):
    """Additional meet & greet charges for responses."""

    pass


class MeetGreet(MeetGreetBase, ResponseModel):
    """Meet & greet option for responses."""

    pass


class CarClassPrice(PriceBase, ResponseModel):
    """Car class pricing information for responses."""

    pass


class Reservation(ReservationBase, ResponseModel):
    """Basic reservation information for responses."""

    pass


# Pure Response Models
class ReservationData(ResponseModel):
    """Editable reservation data returned in get reservation response."""

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


class PriceResponse(ResponseModel):
    """Response from get prices."""

    token: str
    prices: list[CarClassPrice]


class DetailsResponse(ResponseModel):
    """Response from set details."""

    price: float
    breakdown: list[BreakdownItem]


class BookResponse(ResponseModel):
    """Response from book reservation."""

    reservation_id: str


class ListReservationsResponse(ResponseModel):
    """Response from list reservations."""

    success: bool
    reservations: list[Reservation] = Field(default_factory=list)
    error: Optional[str] = None


class GetReservationResponse(ResponseModel):
    """Response from get reservation."""

    reservation: "ReservationData"
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


class EditReservationResponse(ResponseModel):
    """Response from edit reservation."""

    success: bool
