"""Pricing service for getting quotes and updating trip details."""

from ..schemas import (
    DetailsRequest,
    DetailsResponse,
    PriceRequest,
    PriceResponse,
)
from ..transport.base import AsyncBaseTransport, BaseTransport


class AsyncPricingService:
    """Async pricing service."""

    def __init__(self, transport: AsyncBaseTransport):
        self._transport = transport

    async def quote(self, request: PriceRequest) -> PriceResponse:
        """
        Get pricing for a trip.

        Args:
            request: Complete pricing request with all trip details

        Returns:
            PriceResponse with pricing information and session token
        """
        return await self._transport.post("/booking/price/", request, PriceResponse)

    async def update_details(self, request: DetailsRequest) -> DetailsResponse:
        """
        Update reservation details and get updated pricing.

        Args:
            request: Complete details request with token and fields to update

        Returns:
            DetailsResponse with updated pricing
        """
        return await self._transport.post("/booking/details/", request, DetailsResponse)


class PricingService:
    """Sync pricing service."""

    def __init__(self, transport: BaseTransport):
        self._transport = transport

    def quote(self, request: PriceRequest) -> PriceResponse:
        """
        Get pricing for a trip.

        Args:
            request: Complete pricing request with all trip details

        Returns:
            PriceResponse with pricing information and session token
        """
        return self._transport.post("/booking/price/", request, PriceResponse)

    def update_details(self, request: DetailsRequest) -> DetailsResponse:
        """
        Update reservation details and get updated pricing.

        Args:
            request: Complete details request with token and fields to update

        Returns:
            DetailsResponse with updated pricing
        """
        return self._transport.post("/booking/details/", request, DetailsResponse)
