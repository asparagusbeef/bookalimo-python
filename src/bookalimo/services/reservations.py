"""Reservations service for listing, getting, editing, and booking reservations."""

from ..schemas import (
    BookRequest,
    BookResponse,
    EditReservationRequest,
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

    async def edit(self, request: EditReservationRequest) -> EditReservationResponse:
        """
        Edit or cancel a reservation.

        Args:
            request: Complete edit request with confirmation and fields to change

        Returns:
            EditReservationResponse
        """
        return await self._transport.post(
            "/booking/edit/", request, EditReservationResponse
        )

    async def book(self, request: BookRequest) -> BookResponse:
        """
        Book a reservation.

        Args:
            request: Complete booking request with token and payment details

        Returns:
            BookResponse with reservation_id
        """
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

    def edit(self, request: EditReservationRequest) -> EditReservationResponse:
        """
        Edit or cancel a reservation.

        Args:
            request: Complete edit request with confirmation and fields to change

        Returns:
            EditReservationResponse
        """
        return self._transport.post("/booking/edit/", request, EditReservationResponse)

    def book(self, request: BookRequest) -> BookResponse:
        """
        Book a reservation.

        Args:
            request: Complete booking request with token and payment details

        Returns:
            BookResponse with reservation_id
        """
        return self._transport.post("/booking/book/", request, BookResponse)
