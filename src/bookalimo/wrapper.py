"""
High-level API wrapper for Book-A-Limo operations.
Provides clean, LLM-friendly functions that abstract API complexities.
"""

from types import TracebackType
from typing import Any, Optional

from httpx import AsyncClient

from ._client import BookALimoClient
from .exceptions import BookALimoError
from .models import (
    Address,
    Airport,
    BookRequest,
    BookResponse,
    CardHolderType,
    City,
    Credentials,
    CreditCard,
    DetailsRequest,
    DetailsResponse,
    EditableReservationRequest,
    EditReservationResponse,
    GetReservationResponse,
    ListReservationsResponse,
    Location,
    LocationType,
    Passenger,
    PriceRequest,
    PriceResponse,
    RateType,
    Stop,
)


class BookALimo:
    """
    High-level wrapper for Book-A-Limo API operations.
    Provides small, LLM-friendly functions that map 1:1 to API endpoints.
    """

    def __init__(
        self,
        credentials: Credentials,
        http_client: Optional[AsyncClient] = None,
        base_url: str = "https://api.bookalimo.com",
        http_timeout: float = 5.0,
        **kwargs: Any,
    ):
        """
        Initializes the BookALimo API wrapper.

        Args:
            credentials: User ID and password hash for authentication.
            http_client: Optional custom httpx.AsyncClient instance.
            **kwargs: Additional options passed to the BookALimoClient.
        """
        self._owns_http_client = http_client is None
        self.http_client = http_client or AsyncClient()
        self.client = BookALimoClient(
            credentials=credentials,
            client=self.http_client,
            base_url=base_url,
            http_timeout=http_timeout,
            **kwargs,
        )

    async def aclose(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_http_client and not self.http_client.is_closed:
            await self.http_client.aclose()

    async def __aenter__(self) -> "BookALimo":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit."""
        await self.aclose()

    async def list_reservations(
        self, is_archive: bool = False
    ) -> ListReservationsResponse:
        """
        List reservations for the user.

        Args:
            is_archive: If True, fetch archived reservations

        Returns:
            Dict with 'success', 'reservations' list, optional 'error'
        """
        try:
            result = await self.client.list_reservations(is_archive)

            return result
        except Exception as e:
            raise BookALimoError(f"Failed to list reservations: {str(e)}") from e

    async def get_reservation(self, confirmation: str) -> GetReservationResponse:
        """
        Get detailed reservation information.

        Args:
            confirmation: Confirmation number

        Returns:
            Dict with reservation details, status, policies, breakdown
        """
        try:
            result = await self.client.get_reservation(confirmation)

            return result
        except Exception as e:
            raise BookALimoError(f"Failed to get reservation: {str(e)}") from e

    async def get_prices(
        self,
        rate_type: RateType,
        date_time: str,
        pickup: Location,
        dropoff: Location,
        passengers: int,
        luggage: int,
        **kwargs: Any,
    ) -> PriceResponse:
        """
        Get pricing for a trip.

        Args:
            rate_type: 0=P2P, 1=Hourly (or string names)
            date_time: 'MM/dd/yyyy hh:mm tt' format
            pickup_location: Location dict
            dropoff_location: Location dict
            passengers: Number of passengers
            luggage: Number of luggage pieces
            **kwargs: Optional fields like stops, account, car_class_code, etc.

        Returns:
            Dict with 'token' and 'prices' list
        """
        try:
            # Build request with optional fields
            request_data: dict[str, Any] = {
                "rate_type": rate_type,
                "date_time": date_time,
                "pickup": pickup,
                "dropoff": dropoff,
                "passengers": passengers,
                "luggage": luggage,
            }

            # Add optional fields if provided
            optional_fields = [
                "hours",
                "stops",
                "account",
                "passenger",
                "rewards",
                "car_class_code",
                "pets",
                "car_seats",
                "boosters",
                "infants",
                "customer_comment",
            ]

            for field in optional_fields:
                if field in kwargs and kwargs[field] is not None:
                    request_data[field] = kwargs[field]

            request_model = PriceRequest(**request_data)

            result = await self.client.get_prices(request_model)

            return result
        except Exception as e:
            raise BookALimoError(f"Failed to get prices: {str(e)}") from e

    async def set_details(self, token: str, **details: Any) -> DetailsResponse:
        """
        Set reservation details and get updated pricing.

        Args:
            token: Session token from get_prices
            **details: Fields to update (car_class_code, pickup, dropoff,
                      stops, account, passenger, rewards, pets, car_seats,
                      boosters, infants, customer_comment, ta_fee)

        Returns:
            Dict with 'price' and 'breakdown' list
        """
        try:
            request_data: dict[str, Any] = {"token": token}

            # Add provided details
            for key, value in details.items():
                if value is not None:
                    request_data[key] = value

            request_model = DetailsRequest(**request_data)

            result = await self.client.set_details(request_model)

            return result
        except Exception as e:
            raise BookALimoError(f"Failed to set details: {str(e)}") from e

    async def book(
        self,
        token: str,
        method: Optional[str] = None,
        credit_card: Optional[CreditCard] = None,
        promo: Optional[str] = None,
    ) -> BookResponse:
        """
        Book a reservation.

        Args:
            token: Session token from get_prices/set_details
            method: 'charge' for charge accounts, None for credit card
            credit_card: Credit card dict (required if method is not 'charge')
            promo: Optional promo code

        Returns:
            Dict with 'reservation_id'
        """
        try:
            request_data: dict[str, Any] = {"token": token}

            if promo:
                request_data["promo"] = promo

            if method == "charge":
                request_data["method"] = "charge"
            elif credit_card:
                request_data["credit_card"] = credit_card
            else:
                raise BookALimoError(
                    "Either method='charge' or credit_card must be provided"
                )

            request_model = BookRequest(**request_data)

            result = await self.client.book_reservation(request_model)

            return result
        except Exception as e:
            raise BookALimoError(f"Failed to book reservation: {str(e)}") from e

    async def edit_reservation(
        self, confirmation: str, is_cancel_request: bool = False, **changes: Any
    ) -> EditReservationResponse:
        """
        Edit or cancel a reservation.

        Args:
            confirmation: Confirmation number
            is_cancel_request: True to cancel the reservation
            **changes: Fields to change (rate_type, pickup_date, pickup_time,
                      stops, passengers, luggage, pets, car_seats, boosters,
                      infants, other)

        Returns:
            EditReservationResponse
        """
        try:
            request_data: dict[str, Any] = {
                "confirmation": confirmation,
                "is_cancel_request": is_cancel_request,
            }

            # Add changes if not canceling
            if not is_cancel_request:
                for key, value in changes.items():
                    if value is not None:
                        request_data[key] = value

            request_model = EditableReservationRequest(**request_data)

            return await self.client.edit_reservation(request_model)
        except Exception as e:
            raise BookALimoError(f"Failed to edit reservation: {str(e)}") from e


# Convenience functions for creating common data structures


def create_credentials(
    user_id: str, password: str, is_customer: bool = False
) -> Credentials:
    """Create credentials dict with proper password hash."""
    return Credentials(
        id=user_id,
        is_customer=is_customer,
        password_hash=Credentials.create_hash(password, user_id),
    )


def create_address_location(
    address: str,
    google_geocode: Optional[dict[str, Any]] = None,
    district: Optional[str] = None,
    building: Optional[str] = None,
    suite: Optional[str] = None,
    zip_code: Optional[str] = None,
) -> Location:
    """Create address-based location dict."""
    return Location(
        type=LocationType.ADDRESS,
        address=Address(
            city=City(
                city_name=address,
                country_code="US",
                state_code="NY",
                state_name="New York",
            ),
            district=district,
            suite=suite,
            google_geocode=google_geocode,
            place_name=address if not google_geocode else None,
            street_name=address if not google_geocode else None,
            neighbourhood=district,
            building=building,
            zip=zip_code,
        ),
    )


def create_airport_location(
    iata_code: str,
    city_name: str,
    airline_code: Optional[str] = None,
    flight_number: Optional[str] = None,
    terminal: Optional[str] = None,
    meet_greet: Optional[int] = None,
    airline_icao_code: Optional[str] = None,
) -> Location:
    """Create airport-based location dict."""
    return Location(
        type=LocationType.AIRPORT,
        airport=Airport(
            iata_code=iata_code,
            country_code="US",
            state_code="NY",
            airline_iata_code=airline_code,
            airline_icao_code=airline_icao_code,
            flight_number=flight_number,
            terminal=terminal,
            arriving_from_city=City(
                city_name=city_name,
                country_code="US",
                state_code="NY",
                state_name="New York",
            ),
            meet_greet=meet_greet,
        ),
    )


def create_stop(description: str, is_en_route: bool = True) -> Stop:
    """Create stop dict."""
    return Stop(description=description, is_en_route=is_en_route)


def create_passenger(
    first_name: str, last_name: str, phone: str, email: Optional[str] = None
) -> Passenger:
    """Create passenger dict."""
    return Passenger(
        first_name=first_name, last_name=last_name, phone=phone, email=email
    )


def create_credit_card(
    number: str,
    card_holder: str,
    holder_type: CardHolderType,
    expiration: str,
    cvv: str,
    zip_code: Optional[str] = None,
) -> CreditCard:
    """Create credit card dict."""
    return CreditCard(
        number=number,
        card_holder=card_holder,
        holder_type=holder_type,
        expiration=expiration,
        cvv=cvv,
        zip=zip_code,
    )
