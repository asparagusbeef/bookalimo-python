"""Reservations service for listing, getting, editing, and booking reservations."""

from typing import Any, Optional

from ..exceptions import BookalimoRequestError
from ..schemas.booking import (
    BookRequest,
    BookResponse,
    CreditCard,
    EditableReservationRequest,
    EditReservationResponse,
    GetReservationRequest,
    GetReservationResponse,
    ListReservationsRequest,
    ListReservationsResponse,
)
from ..transport.base import AsyncBaseTransport, BaseTransport


class AsyncReservationsService:
    """Async reservations service."""

    def __init__(self, transport: AsyncBaseTransport):
        self._transport = transport

    async def list(self, is_archive: bool = False) -> ListReservationsResponse:
        """
        List reservations for the user.

        Args:
            is_archive: If True, fetch archived reservations

        Returns:
            ListReservationsResponse with reservations list
        """
        request = ListReservationsRequest(is_archive=is_archive)
        return await self._transport.post(
            "/booking/reservation/list/", request, ListReservationsResponse
        )

    async def get(self, confirmation: str) -> GetReservationResponse:
        """
        Get detailed reservation information.

        Args:
            confirmation: Confirmation number

        Returns:
            GetReservationResponse with reservation details
        """
        request = GetReservationRequest(confirmation=confirmation)
        return await self._transport.post(
            "/booking/reservation/get/", request, GetReservationResponse
        )

    async def edit(
        self, confirmation: str, *, is_cancel: bool = False, **changes: Any
    ) -> EditReservationResponse:
        """
        Edit or cancel a reservation.

        Args:
            confirmation: Confirmation number
            is_cancel: True to cancel the reservation
            **changes: Fields to change (rate_type, pickup_date, pickup_time,
                      stops, passengers, luggage, pets, car_seats, boosters,
                      infants, other)

        Returns:
            EditReservationResponse
        """
        request_data = {
            "confirmation": confirmation,
            "is_cancel_request": is_cancel,
        }

        # Add changes if not canceling
        if not is_cancel:
            for key, value in changes.items():
                if value is not None:
                    request_data[key] = value

        request = EditableReservationRequest.model_validate(request_data)
        return await self._transport.post(
            "/booking/edit/", request, EditReservationResponse
        )

    async def book(
        self,
        token: str,
        *,
        method: Optional[str] = None,
        credit_card: Optional[CreditCard] = None,
        promo: Optional[str] = None,
    ) -> BookResponse:
        """
        Book a reservation.

        Args:
            token: Session token from pricing.quote() or pricing.update_details()
            method: 'charge' for charge accounts, None for credit card
            credit_card: Credit card information (required if method is not 'charge')
            promo: Optional promo code

        Returns:
            BookResponse with reservation_id
        """
        request_data: dict[str, Any] = {"token": token}

        if promo:
            request_data["promo"] = promo

        if method == "charge":
            request_data["method"] = "charge"
        elif credit_card:
            request_data["credit_card"] = credit_card
        else:
            raise BookalimoRequestError(
                "Either method='charge' or credit_card must be provided"
            )

        request = BookRequest(**request_data)
        return await self._transport.post("/booking/book/", request, BookResponse)


class ReservationsService:
    """Sync reservations service."""

    def __init__(self, transport: BaseTransport):
        self._transport = transport

    def list(self, is_archive: bool = False) -> ListReservationsResponse:
        """
        List reservations for the user.

        Args:
            is_archive: If True, fetch archived reservations

        Returns:
            ListReservationsResponse with reservations list
        """
        request = ListReservationsRequest(is_archive=is_archive)
        return self._transport.post(
            "/booking/reservation/list/", request, ListReservationsResponse
        )

    def get(self, confirmation: str) -> GetReservationResponse:
        """
        Get detailed reservation information.

        Args:
            confirmation: Confirmation number

        Returns:
            GetReservationResponse with reservation details
        """
        request = GetReservationRequest(confirmation=confirmation)
        return self._transport.post(
            "/booking/reservation/get/", request, GetReservationResponse
        )

    def edit(
        self, confirmation: str, *, is_cancel: bool = False, **changes: Any
    ) -> EditReservationResponse:
        """
        Edit or cancel a reservation.

        Args:
            confirmation: Confirmation number
            is_cancel: True to cancel the reservation
            **changes: Fields to change (rate_type, pickup_date, pickup_time,
                      stops, passengers, luggage, pets, car_seats, boosters,
                      infants, other)

        Returns:
            EditReservationResponse
        """
        request_data = {
            "confirmation": confirmation,
            "is_cancel_request": is_cancel,
        }

        # Add changes if not canceling
        if not is_cancel:
            for key, value in changes.items():
                if value is not None:
                    request_data[key] = value

        request = EditableReservationRequest.model_validate(request_data)
        return self._transport.post("/booking/edit/", request, EditReservationResponse)

    def book(
        self,
        token: str,
        *,
        method: Optional[str] = None,
        credit_card: Optional[CreditCard] = None,
        promo: Optional[str] = None,
    ) -> BookResponse:
        """
        Book a reservation.

        Args:
            token: Session token from pricing.quote() or pricing.update_details()
            method: 'charge' for charge accounts, None for credit card
            credit_card: Credit card information (required if method is not 'charge')
            promo: Optional promo code

        Returns:
            BookResponse with reservation_id
        """
        request_data: dict[str, Any] = {"token": token}

        if promo:
            request_data["promo"] = promo

        if method == "charge":
            request_data["method"] = "charge"
        elif credit_card:
            request_data["credit_card"] = credit_card
        else:
            raise BookalimoRequestError(
                "Either method='charge' or credit_card must be provided"
            )

        request = BookRequest.model_validate(request_data)
        return self._transport.post("/booking/book/", request, BookResponse)
