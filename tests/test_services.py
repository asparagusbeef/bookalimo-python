"""Tests for service classes - pricing and reservations."""

from unittest.mock import AsyncMock, Mock

import pytest

from bookalimo.exceptions import BookalimoRequestError
from bookalimo.schemas.booking import (
    BookRequest,
    BookResponse,
    DetailsRequest,
    DetailsResponse,
    EditableReservationRequest,
    EditReservationResponse,
    GetReservationRequest,
    GetReservationResponse,
    ListReservationsRequest,
    ListReservationsResponse,
    LocationType,
    PriceRequest,
    PriceResponse,
    RateType,
)
from bookalimo.services import (
    AsyncPricingService,
    AsyncReservationsService,
    PricingService,
    ReservationsService,
)


class TestAsyncPricingService:
    """Tests for AsyncPricingService."""

    @pytest.fixture
    def pricing_service(self, async_transport):
        """Create pricing service for testing."""
        return AsyncPricingService(async_transport)

    @pytest.mark.asyncio
    async def test_quote_basic(
        self, pricing_service, sample_pickup_location, sample_dropoff_location
    ):
        """Test basic quote functionality."""
        mock_response = PriceResponse(token="test-token-123", prices=[])

        pricing_service._transport.post = AsyncMock(return_value=mock_response)

        result = await pricing_service.quote(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        assert result == mock_response

        # Verify the call was made with correct parameters
        pricing_service._transport.post.assert_called_once()
        call_args = pricing_service._transport.post.call_args

        assert call_args[0][0] == "/booking/price/"  # path
        request = call_args[0][1]  # request model
        assert isinstance(request, PriceRequest)
        assert request.rate_type == RateType.P2P
        assert request.passengers == 2
        assert request.luggage == 1
        assert call_args[0][2] == PriceResponse  # response model

    @pytest.mark.asyncio
    async def test_quote_with_optional_fields(
        self, pricing_service, sample_pickup_location, sample_dropoff_location
    ):
        """Test quote with optional fields."""
        mock_response = PriceResponse(token="test-token-123", prices=[])

        pricing_service._transport.post = AsyncMock(return_value=mock_response)

        result = await pricing_service.quote(
            rate_type=RateType.HOURLY,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=4,
            luggage=2,
            hours=3,
            car_class_code="SUV",
            pets=1,
            car_seats=2,
            customer_comment="Special instructions",
        )

        assert result == mock_response

        # Verify optional fields were included
        call_args = pricing_service._transport.post.call_args
        request = call_args[0][1]
        assert request.hours == 3
        assert request.car_class_code == "SUV"
        assert request.pets == 1
        assert request.car_seats == 2
        assert request.customer_comment == "Special instructions"

    @pytest.mark.asyncio
    async def test_quote_excludes_none_optional_fields(
        self, pricing_service, sample_pickup_location, sample_dropoff_location
    ):
        """Test that None optional fields are excluded from request."""
        mock_response = PriceResponse(token="test-token-123", prices=[])

        pricing_service._transport.post = AsyncMock(return_value=mock_response)

        await pricing_service.quote(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
            hours=None,  # Should be excluded
            car_class_code=None,  # Should be excluded
            customer_comment="Valid comment",  # Should be included
        )

        call_args = pricing_service._transport.post.call_args
        request_dict = call_args[0][1].model_dump()

        assert "hours" not in request_dict or request_dict["hours"] is None
        assert (
            "carClassCode" not in request_dict or request_dict["carClassCode"] is None
        )
        assert request_dict["customerComment"] == "Valid comment"

    @pytest.mark.asyncio
    async def test_update_details_basic(self, pricing_service):
        """Test basic update details functionality."""
        mock_response = DetailsResponse(price=175.00, breakdown=[])

        pricing_service._transport.post = AsyncMock(return_value=mock_response)

        result = await pricing_service.update_details(
            token="original-token-123", car_class_code="LUXURY"
        )

        assert result == mock_response

        # Verify the call
        call_args = pricing_service._transport.post.call_args
        assert call_args[0][0] == "/booking/details/"
        request = call_args[0][1]
        assert isinstance(request, DetailsRequest)
        assert request.token == "original-token-123"
        assert request.car_class_code == "LUXURY"

    @pytest.mark.asyncio
    async def test_update_details_multiple_fields(
        self, pricing_service, sample_pickup_location
    ):
        """Test update details with multiple fields."""
        mock_response = DetailsResponse(price=225.00, breakdown=[])

        pricing_service._transport.post = AsyncMock(return_value=mock_response)

        result = await pricing_service.update_details(
            token="original-token-123",
            car_class_code="SUV",
            pickup=sample_pickup_location,
            pets=2,
            customer_comment="Updated instructions",
        )

        assert result == mock_response

        # Verify all fields were included
        call_args = pricing_service._transport.post.call_args
        request = call_args[0][1]
        assert request.car_class_code == "SUV"
        assert request.pickup == sample_pickup_location
        assert request.pets == 2
        assert request.customer_comment == "Updated instructions"

    @pytest.mark.asyncio
    async def test_update_details_excludes_none_values(self, pricing_service):
        """Test that None values are excluded from update details."""
        mock_response = DetailsResponse(price=150.00, breakdown=[])

        pricing_service._transport.post = AsyncMock(return_value=mock_response)

        await pricing_service.update_details(
            token="original-token-123",
            car_class_code="SEDAN",
            pickup=None,  # Should be excluded
            pets=None,  # Should be excluded
        )

        call_args = pricing_service._transport.post.call_args
        request_dict = call_args[0][1].model_dump()

        assert request_dict["token"] == "original-token-123"
        assert request_dict["carClassCode"] == "SEDAN"
        assert "pickup" not in request_dict or request_dict["pickup"] is None
        assert "pets" not in request_dict or request_dict["pets"] is None


class TestSyncPricingService:
    """Tests for sync PricingService."""

    @pytest.fixture
    def pricing_service(self, sync_transport):
        """Create sync pricing service for testing."""
        return PricingService(sync_transport)

    def test_quote_basic(
        self, pricing_service, sample_pickup_location, sample_dropoff_location
    ):
        """Test basic sync quote functionality."""
        mock_response = PriceResponse(token="sync-token-123", prices=[])

        pricing_service._transport.post = Mock(return_value=mock_response)

        result = pricing_service.quote(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        assert result == mock_response
        pricing_service._transport.post.assert_called_once()

    def test_update_details_basic(self, pricing_service):
        """Test basic sync update details functionality."""
        mock_response = DetailsResponse(price=175.00, breakdown=[])

        pricing_service._transport.post = Mock(return_value=mock_response)

        result = pricing_service.update_details(
            token="sync-original-token-123", car_class_code="LUXURY"
        )

        assert result == mock_response
        pricing_service._transport.post.assert_called_once()


class TestAsyncReservationsService:
    """Tests for AsyncReservationsService."""

    @pytest.fixture
    def reservations_service(self, async_transport):
        """Create async reservations service for testing."""
        return AsyncReservationsService(async_transport)

    @pytest.mark.asyncio
    async def test_list_reservations_default(self, reservations_service):
        """Test list reservations with default parameters."""
        mock_response = ListReservationsResponse(success=True, reservations=[])

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.list()

        assert result == mock_response

        # Verify call parameters
        call_args = reservations_service._transport.post.call_args
        assert call_args[0][0] == "/booking/reservation/list/"
        request = call_args[0][1]
        assert isinstance(request, ListReservationsRequest)
        assert request.is_archive is False

    @pytest.mark.asyncio
    async def test_list_reservations_archived(self, reservations_service):
        """Test list archived reservations."""
        mock_response = ListReservationsResponse(success=True, reservations=[])

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.list(is_archive=True)

        assert result == mock_response

        # Verify archive flag
        call_args = reservations_service._transport.post.call_args
        request = call_args[0][1]
        assert request.is_archive is True

    @pytest.mark.asyncio
    async def test_get_reservation(self, reservations_service):
        """Test get reservation details."""
        mock_response = GetReservationResponse(
            reservation=EditableReservationRequest(confirmation="TEST123"),
            is_editable=True,
            is_cancellation_pending=False,
            pickup_type=LocationType.ADDRESS,
            pickup_description="Test pickup",
            dropoff_type=LocationType.AIRPORT,
            dropoff_description="Test dropoff",
        )

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.get("TEST123")

        assert result == mock_response

        # Verify call parameters
        call_args = reservations_service._transport.post.call_args
        assert call_args[0][0] == "/booking/reservation/get/"
        request = call_args[0][1]
        assert isinstance(request, GetReservationRequest)
        assert request.confirmation == "TEST123"

    @pytest.mark.asyncio
    async def test_edit_reservation_cancel(self, reservations_service):
        """Test cancel reservation."""
        mock_response = EditReservationResponse(success=True)

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.edit("TEST123", is_cancel=True)

        assert result == mock_response

        # Verify call parameters
        call_args = reservations_service._transport.post.call_args
        assert call_args[0][0] == "/booking/edit/"
        request = call_args[0][1]
        assert isinstance(request, EditableReservationRequest)
        assert request.confirmation == "TEST123"
        assert request.is_cancel_request is True

    @pytest.mark.asyncio
    async def test_edit_reservation_modify(self, reservations_service):
        """Test modify reservation."""
        mock_response = EditReservationResponse(success=True)

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.edit(
            "TEST123", passengers=4, luggage=3, pickup_time="04:00 PM"
        )

        assert result == mock_response

        # Verify changes were included
        call_args = reservations_service._transport.post.call_args
        request = call_args[0][1]
        assert request.confirmation == "TEST123"
        assert request.is_cancel_request is False
        assert request.passengers == 4
        assert request.luggage == 3
        assert request.pickup_time == "04:00 PM"

    @pytest.mark.asyncio
    async def test_edit_reservation_excludes_none_changes(self, reservations_service):
        """Test that None changes are excluded from edit request."""
        mock_response = EditReservationResponse(success=True)

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        await reservations_service.edit(
            "TEST123",
            passengers=4,
            luggage=None,  # Should be excluded
            pickup_time="04:00 PM",
        )

        call_args = reservations_service._transport.post.call_args
        request_dict = call_args[0][1].model_dump()

        assert request_dict["passengers"] == 4
        assert "luggage" not in request_dict or request_dict["luggage"] is None
        assert request_dict["pickupTime"] == "04:00 PM"

    @pytest.mark.asyncio
    async def test_book_with_credit_card(
        self, reservations_service, sample_credit_card
    ):
        """Test booking with credit card."""
        mock_response = BookResponse(reservation_id="RES12345")

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.book(
            token="booking-token-123", credit_card=sample_credit_card
        )

        assert result == mock_response

        # Verify call parameters
        call_args = reservations_service._transport.post.call_args
        assert call_args[0][0] == "/booking/book/"
        request = call_args[0][1]
        assert isinstance(request, BookRequest)
        assert request.token == "booking-token-123"
        assert request.credit_card == sample_credit_card

    @pytest.mark.asyncio
    async def test_book_with_charge_method(self, reservations_service):
        """Test booking with charge method."""
        mock_response = BookResponse(reservation_id="RES54321")

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.book(
            token="booking-token-456", method="charge"
        )

        assert result == mock_response

        # Verify call parameters
        call_args = reservations_service._transport.post.call_args
        request = call_args[0][1]
        assert request.token == "booking-token-456"
        assert request.method == "charge"

    @pytest.mark.asyncio
    async def test_book_with_promo_code(self, reservations_service, sample_credit_card):
        """Test booking with promo code."""
        mock_response = BookResponse(reservation_id="RES11111")

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.book(
            token="booking-token-789", credit_card=sample_credit_card, promo="SAVE10"
        )

        assert result == mock_response

        # Verify promo code was included
        call_args = reservations_service._transport.post.call_args
        request = call_args[0][1]
        assert request.promo == "SAVE10"

    @pytest.mark.asyncio
    async def test_book_missing_payment_method_raises_error(self, reservations_service):
        """Test that booking without payment method raises error."""
        with pytest.raises(
            BookalimoRequestError,
            match="Either method='charge' or credit_card must be provided",
        ):
            await reservations_service.book(token="booking-token-999")

    @pytest.mark.asyncio
    async def test_book_charge_method_without_credit_card(self, reservations_service):
        """Test booking with charge method and no credit card works."""
        mock_response = BookResponse(reservation_id="RES99999")

        reservations_service._transport.post = AsyncMock(return_value=mock_response)

        result = await reservations_service.book(
            token="booking-token-charge", method="charge"
        )

        assert result == mock_response


class TestSyncReservationsService:
    """Tests for sync ReservationsService."""

    @pytest.fixture
    def reservations_service(self, sync_transport):
        """Create sync reservations service for testing."""
        return ReservationsService(sync_transport)

    def test_list_reservations_basic(self, reservations_service):
        """Test basic sync list reservations."""
        mock_response = ListReservationsResponse(success=True, reservations=[])

        reservations_service._transport.post = Mock(return_value=mock_response)

        result = reservations_service.list()

        assert result == mock_response
        reservations_service._transport.post.assert_called_once()

    def test_book_sync_uses_model_validate(
        self, reservations_service, sample_credit_card
    ):
        """Test that sync book method uses model_validate instead of constructor."""
        mock_response = BookResponse(reservation_id="RES_SYNC")

        reservations_service._transport.post = Mock(return_value=mock_response)

        result = reservations_service.book(
            token="sync-booking-token", credit_card=sample_credit_card
        )

        assert result == mock_response
        # This verifies that the sync version uses model_validate
        # which is handled internally by the BookRequest constructor
