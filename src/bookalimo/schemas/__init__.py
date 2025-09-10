"""Pydantic schemas for the Bookalimo SDK."""

from ..transport.auth import Credentials
from .places import (
    AutocompletePlacesRequest,
    AutocompletePlacesResponse,
    BusinessStatus,
    Circle,
    EVConnectorType,
    FieldMaskInput,
    FormattableText,
    GeocodingRequest,
    GetPlaceRequest,
    GooglePlace,
    LocationBias,
    LocationRestriction,
    Place,
    PlacePrediction,
    PlaceType,
    PriceLevel,
    QueryPrediction,
    RankPreference,
    SearchTextRequest,
    StringRange,
    StructuredFormat,
    Suggestion,
)

# Import request models (for API calls - serialize to camelCase)
from .requests import (
    Account,
    Address,
    Airport,
    BookRequest,
    City,
    CreditCard,
    DetailsRequest,
    EditReservationRequest,
    GetReservationRequest,
    ListReservationsRequest,
    Location,
    MeetGreetAdditional,
    Passenger,
    Price,
    PriceRequest,
    Reservation,
    Reward,
    Stop,
)

# Import response versions with explicit naming for clarity
from .responses import (
    Account as AccountResponse,
)
from .responses import (
    Address as AddressResponse,
)
from .responses import (
    Airport as AirportResponse,
)

# Import response models (from API responses - serialize to snake_case)
from .responses import (
    BookResponse,
    CarClassPrice,
    DetailsResponse,
    EditReservationResponse,
    GetReservationResponse,
    ListReservationsResponse,
    PriceResponse,
    ReservationData,
)
from .responses import (
    BreakdownItem as BreakdownItemResponse,
)
from .responses import (
    City as CityResponse,
)
from .responses import (
    CreditCard as CreditCardResponse,
)
from .responses import (
    Location as LocationResponse,
)
from .responses import (
    MeetGreet as MeetGreetResponse,
)
from .responses import (
    MeetGreetAdditional as MeetGreetAdditionalResponse,
)
from .responses import (
    Passenger as PassengerResponse,
)
from .responses import (
    Reservation as ReservationResponse,
)
from .responses import (
    Reward as RewardResponse,
)
from .responses import (
    Stop as StopResponse,
)

# Import enums and shared types from shared module
from .shared import (
    CardHolderType,
    LocationType,
    MeetGreetType,
    RateType,
    ReservationStatus,
    RewardType,
)

__all__ = [
    # Enums and shared types
    "RateType",
    "LocationType",
    "MeetGreetType",
    "RewardType",
    "ReservationStatus",
    "CardHolderType",
    # Request models (default exports - serialize to camelCase for API)
    "City",
    "Address",
    "Airport",
    "Location",
    "Stop",
    "Account",
    "Passenger",
    "Reward",
    "CreditCard",
    "MeetGreetAdditional",
    "Price",
    "Reservation",
    "EditReservationRequest",
    "PriceRequest",
    "DetailsRequest",
    "BookRequest",
    "ListReservationsRequest",
    "GetReservationRequest",
    # Response models (serialize to snake_case for Python DX)
    "BookResponse",
    "CarClassPrice",
    "DetailsResponse",
    "EditReservationResponse",
    "GetReservationResponse",
    "ListReservationsResponse",
    "PriceResponse",
    # Explicit response model variants (for handling API responses)
    "AccountResponse",
    "AddressResponse",
    "AirportResponse",
    "BreakdownItemResponse",
    "CityResponse",
    "CreditCardResponse",
    "ReservationData",
    "LocationResponse",
    "MeetGreetResponse",
    "MeetGreetAdditionalResponse",
    "PassengerResponse",
    "ReservationResponse",
    "RewardResponse",
    "StopResponse",
    # Places API schemas
    "PlaceType",
    "RankPreference",
    "EVConnectorType",
    "StringRange",
    "FormattableText",
    "StructuredFormat",
    "Circle",
    "LocationBias",
    "LocationRestriction",
    "Place",
    "AutocompletePlacesResponse",
    "PlacePrediction",
    "QueryPrediction",
    "Suggestion",
    "GetPlaceRequest",
    "AutocompletePlacesRequest",
    "GeocodingRequest",
    "SearchTextRequest",
    "GooglePlace",
    "PriceLevel",
    "FieldMaskInput",
    "BusinessStatus",
    # Auth
    "Credentials",
]
