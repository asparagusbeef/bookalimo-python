"""Pricing service for getting quotes and updating trip details."""

from typing import Any

from ..schemas.booking import (
    DetailsRequest,
    DetailsResponse,
    Location,
    PriceRequest,
    PriceResponse,
    RateType,
)
from ..transport.base import AsyncBaseTransport, BaseTransport


class AsyncPricingService:
    """Async pricing service."""

    def __init__(self, transport: AsyncBaseTransport):
        self._transport = transport

    async def quote(
        self,
        rate_type: RateType,
        date_time: str,
        pickup: Location,
        dropoff: Location,
        passengers: int,
        luggage: int,
        **opts: Any,
    ) -> PriceResponse:
        """
        Get pricing for a trip.

        Args:
            rate_type: Rate type (P2P, HOURLY, etc.)
            date_time: Date and time in 'MM/dd/yyyy hh:mm tt' format
            pickup: Pickup location
            dropoff: Dropoff location
            passengers: Number of passengers
            luggage: Number of luggage pieces
            **opts: Optional fields like hours, stops, account, car_class_code,
                   passenger, rewards, pets, car_seats, boosters, infants,
                   customer_comment

        Returns:
            PriceResponse with pricing information and session token
        """
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
            if field in opts and opts[field] is not None:
                request_data[field] = opts[field]

        request = PriceRequest(**request_data)
        return await self._transport.post("/booking/price/", request, PriceResponse)

    async def update_details(self, token: str, **details: Any) -> DetailsResponse:
        """
        Update reservation details and get updated pricing.

        Args:
            token: Session token from quote()
            **details: Fields to update (car_class_code, pickup, dropoff,
                      stops, account, passenger, rewards, pets, car_seats,
                      boosters, infants, customer_comment, ta_fee)

        Returns:
            DetailsResponse with updated pricing
        """
        request_data: dict[str, Any] = {"token": token}

        # Add provided details
        for key, value in details.items():
            if value is not None:
                request_data[key] = value

        request = DetailsRequest(**request_data)
        return await self._transport.post("/booking/details/", request, DetailsResponse)


class PricingService:
    """Sync pricing service."""

    def __init__(self, transport: BaseTransport):
        self._transport = transport

    def quote(
        self,
        rate_type: RateType,
        date_time: str,
        pickup: Location,
        dropoff: Location,
        passengers: int,
        luggage: int,
        **opts: Any,
    ) -> PriceResponse:
        """
        Get pricing for a trip.

        Args:
            rate_type: Rate type (P2P, HOURLY, etc.)
            date_time: Date and time in 'MM/dd/yyyy hh:mm tt' format
            pickup: Pickup location
            dropoff: Location
            passengers: Number of passengers
            luggage: Number of luggage pieces
            **opts: Optional fields like hours, stops, account, car_class_code,
                   passenger, rewards, pets, car_seats, boosters, infants,
                   customer_comment

        Returns:
            PriceResponse with pricing information and session token
        """
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
            if field in opts and opts[field] is not None:
                request_data[field] = opts[field]

        request = PriceRequest(**request_data)
        return self._transport.post("/booking/price/", request, PriceResponse)

    def update_details(self, token: str, **details: Any) -> DetailsResponse:
        """
        Update reservation details and get updated pricing.

        Args:
            token: Session token from quote()
            **details: Fields to update (car_class_code, pickup, dropoff,
                      stops, account, passenger, rewards, pets, car_seats,
                      boosters, infants, customer_comment, ta_fee)

        Returns:
            DetailsResponse with updated pricing
        """
        request_data: dict[str, Any] = {"token": token}

        # Add provided details
        for key, value in details.items():
            if value is not None:
                request_data[key] = value

        request = DetailsRequest(**request_data)
        return self._transport.post("/booking/details/", request, DetailsResponse)
