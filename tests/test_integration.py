"""Integration tests for the Bookalimo SDK."""

import asyncio

import httpx
import pytest
import respx

from bookalimo import AsyncBookalimo, Bookalimo
from bookalimo.exceptions import BookalimoHTTPError, BookalimoTimeout
from bookalimo.schemas.booking import (
    BookResponse,
    CreditCard,
    DetailsResponse,
    EditReservationResponse,
    GetReservationResponse,
    ListReservationsResponse,
    Location,
    LocationType,
    PriceResponse,
    RateType,
)
from bookalimo.transport.auth import Credentials


@pytest.mark.integration
class TestEndToEndBookingFlow:
    """Test complete booking flows from start to finish."""

    @pytest.fixture
    def booking_locations(self):
        """Sample locations for booking flow tests."""
        pickup = Location(
            type=LocationType.ADDRESS,
            name="123 Business Ave",
            line1="123 Business Ave",
            line2="Suite 100",
            city="New York",
            state="NY",
            zip_code="10001",
            country="US",
            latitude=40.7128,
            longitude=-74.0060,
        )

        dropoff = Location(
            type=LocationType.AIRPORT,
            name="John F. Kennedy International Airport",
            line1="JFK Airport",
            city="Queens",
            state="NY",
            zip_code="11430",
            country="US",
            airport_code="JFK",
            latitude=40.6413,
            longitude=-73.7781,
        )

        return pickup, dropoff

    @pytest.fixture
    def test_credit_card(self):
        """Test credit card for booking flow."""
        return CreditCard(
            number="4111111111111111",
            exp_month="12",
            exp_year="25",
            cvv="123",
            cardholder_name="John Doe",
            billing_zip="10001",
        )

    @pytest.mark.asyncio
    async def test_complete_async_booking_flow(
        self, booking_locations, test_credit_card
    ):
        """Test complete async booking flow: quote -> update -> book."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create("integration_user", "integration_password")

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock quote response
            quote_response = {
                "token": "integration-token-12345",
                "total": 175.50,
                "base_rate": 150.00,
                "tax": 12.50,
                "tip": 13.00,
                "currency": "USD",
                "car_class_code": "SEDAN",
                "estimated_time": "45 minutes",
                "distance": "25.3 miles",
            }
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            # Mock details update response
            details_response = {
                "token": "integration-updated-token-67890",
                "total": 225.50,
                "base_rate": 200.00,
                "tax": 12.50,
                "tip": 13.00,
                "currency": "USD",
                "car_class_code": "SUV",
            }
            respx_mock.post("/booking/details/").mock(
                return_value=httpx.Response(200, json=details_response)
            )

            # Mock booking response
            book_response = {
                "reservation_id": "RES_INTEGRATION_123",
                "confirmation": "CONF_INTEGRATION_456",
                "success": True,
                "message": "Booking confirmed",
            }
            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(200, json=book_response)
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Step 1: Get initial quote
                quote = await client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/15/2025 03:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=2,
                    customer_comment="Please arrive 10 minutes early",
                )

                assert isinstance(quote, PriceResponse)
                assert quote.token == "integration-token-12345"
                assert quote.total == 175.50
                assert quote.car_class_code == "SEDAN"

                # Step 2: Update details (upgrade car class)
                updated_details = await client.pricing.update_details(
                    token=quote.token,
                    car_class_code="SUV",
                    customer_comment="Upgraded to SUV, please arrive 10 minutes early",
                )

                assert isinstance(updated_details, DetailsResponse)
                assert updated_details.token == "integration-updated-token-67890"
                assert updated_details.total == 225.50
                assert updated_details.car_class_code == "SUV"

                # Step 3: Book the reservation
                booking = await client.reservations.book(
                    token=updated_details.token, credit_card=test_credit_card
                )

                assert isinstance(booking, BookResponse)
                assert booking.reservation_id == "RES_INTEGRATION_123"
                assert booking.confirmation == "CONF_INTEGRATION_456"
                assert booking.success is True

    def test_complete_sync_booking_flow(self, booking_locations, test_credit_card):
        """Test complete sync booking flow: quote -> book with charge method."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create(
            "sync_integration_user", "sync_integration_password"
        )

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock quote response
            quote_response = {
                "token": "sync-integration-token-98765",
                "total": 150.00,
                "base_rate": 125.00,
                "tax": 12.50,
                "tip": 12.50,
                "currency": "USD",
                "car_class_code": "SEDAN",
            }
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            # Mock booking response (charge account)
            book_response = {
                "reservation_id": "RES_SYNC_INTEGRATION_789",
                "confirmation": "CONF_SYNC_INTEGRATION_101",
                "success": True,
            }
            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(200, json=book_response)
            )

            with Bookalimo(credentials=credentials) as client:
                # Step 1: Get quote
                quote = client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/20/2025 02:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=1,
                    luggage=1,
                )

                assert quote.token == "sync-integration-token-98765"
                assert quote.total == 150.00

                # Step 2: Book with charge method (corporate account)
                booking = client.reservations.book(token=quote.token, method="charge")

                assert booking.reservation_id == "RES_SYNC_INTEGRATION_789"
                assert booking.confirmation == "CONF_SYNC_INTEGRATION_101"
                assert booking.success is True

    @pytest.mark.asyncio
    async def test_reservation_management_flow(self):
        """Test complete reservation management flow: list -> get -> edit."""
        credentials = Credentials.create(
            "reservation_mgmt_user", "reservation_mgmt_password"
        )

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock list reservations response
            list_response = {
                "reservations": [
                    {
                        "confirmation": "CONF_MGR_001",
                        "status": "CONFIRMED",
                        "passenger_name": "John Doe",
                        "pickup_date": "2025-09-15",
                        "pickup_time": "15:00",
                    },
                    {
                        "confirmation": "CONF_MGR_002",
                        "status": "PENDING",
                        "passenger_name": "Jane Smith",
                        "pickup_date": "2025-09-16",
                        "pickup_time": "10:00",
                    },
                ],
                "total_count": 2,
            }
            respx_mock.post("/booking/reservation/list/").mock(
                return_value=httpx.Response(200, json=list_response)
            )

            # Mock get reservation response
            get_response = {
                "confirmation": "CONF_MGR_001",
                "status": "CONFIRMED",
                "passenger_name": "John Doe",
                "pickup_date": "2025-09-15",
                "pickup_time": "15:00",
                "pickup_location": "123 Business Ave, New York, NY",
                "dropoff_location": "JFK Airport, Queens, NY",
                "vehicle_type": "SEDAN",
                "total_amount": 175.50,
            }
            respx_mock.post("/booking/reservation/get/").mock(
                return_value=httpx.Response(200, json=get_response)
            )

            # Mock edit reservation response
            edit_response = {
                "success": True,
                "message": "Reservation updated successfully",
                "confirmation": "CONF_MGR_001",
            }
            respx_mock.post("/booking/edit/").mock(
                return_value=httpx.Response(200, json=edit_response)
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Step 1: List active reservations
                reservations = await client.reservations.list()

                assert isinstance(reservations, ListReservationsResponse)
                assert reservations.total_count == 2
                assert len(reservations.reservations) == 2

                # Step 2: Get details of first reservation
                reservation_details = await client.reservations.get("CONF_MGR_001")

                assert isinstance(reservation_details, GetReservationResponse)
                assert reservation_details.confirmation == "CONF_MGR_001"
                assert reservation_details.status == "CONFIRMED"
                assert reservation_details.passenger_name == "John Doe"

                # Step 3: Edit the reservation (change passenger count)
                edit_result = await client.reservations.edit(
                    "CONF_MGR_001",
                    passengers=3,
                    pickup_time="14:30",
                    other="Changed passenger count and pickup time",
                )

                assert isinstance(edit_result, EditReservationResponse)
                assert edit_result.success is True
                assert "updated successfully" in edit_result.message

    @pytest.mark.asyncio
    async def test_error_handling_throughout_flow(self, booking_locations):
        """Test error handling at different stages of booking flow."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create("error_test_user", "error_test_password")

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock quote request that succeeds
            quote_response = {
                "token": "error-test-token-123",
                "total": 100.00,
                "currency": "USD",
            }
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            # Mock details update that fails
            respx_mock.post("/booking/details/").mock(
                return_value=httpx.Response(
                    400,
                    json={"error": "Invalid car class", "code": "INVALID_CAR_CLASS"},
                )
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Step 1: Successful quote
                quote = await client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/25/2025 12:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

                assert quote.token == "error-test-token-123"

                # Step 2: Failed details update should raise proper exception
                with pytest.raises(BookalimoHTTPError) as exc_info:
                    await client.pricing.update_details(
                        token=quote.token, car_class_code="INVALID_CLASS"
                    )

                assert exc_info.value.status_code == 400
                assert "Invalid car class" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_handling_in_flow(self, booking_locations):
        """Test timeout handling during booking flow."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create("timeout_test_user", "timeout_test_password")

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock quote request that times out
            respx_mock.post("/booking/price/").mock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Should handle timeout gracefully
                with pytest.raises(BookalimoTimeout):
                    await client.pricing.quote(
                        rate_type=RateType.P2P,
                        date_time="09/25/2025 12:00 PM",
                        pickup=pickup,
                        dropoff=dropoff,
                        passengers=2,
                        luggage=1,
                    )

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, booking_locations):
        """Test concurrent operations on the same client."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create("concurrent_user", "concurrent_password")

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock different responses for different requests
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "concurrent-token",
                        "total": 150.00,
                        "currency": "USD",
                    },
                )
            )

            respx_mock.post("/booking/reservation/list/").mock(
                return_value=httpx.Response(
                    200, json={"reservations": [], "total_count": 0}
                )
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Run quote and list reservations concurrently
                quote_task = client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="09/25/2025 12:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=1,
                )

                list_task = client.reservations.list()

                # Both should complete successfully
                quote_result, list_result = await asyncio.gather(quote_task, list_task)

                assert quote_result.token == "concurrent-token"
                assert list_result.total_count == 0


@pytest.mark.integration
class TestGooglePlacesIntegration:
    """Integration tests for Google Places functionality."""

    def test_places_integration_with_booking_flow(self, test_credit_card):
        """Test using Google Places to resolve locations for booking."""
        credentials = Credentials.create(
            "places_integration_user", "places_integration_password"
        )

        # This test requires Google Places integration to be available
        try:
            import importlib.util

            if not importlib.util.find_spec("bookalimo.integrations.google_places"):
                raise ImportError
        except ImportError:
            pytest.skip("Google Places integration not available")

        with respx.mock(base_url="https://sandbox.bookalimo.com") as booking_mock:
            # Mock booking API responses
            quote_response = {
                "token": "places-integration-token",
                "total": 200.00,
                "currency": "USD",
            }
            booking_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            book_response = {
                "reservation_id": "RES_PLACES_123",
                "confirmation": "CONF_PLACES_456",
                "success": True,
            }
            booking_mock.post("/booking/book/").mock(
                return_value=httpx.Response(200, json=book_response)
            )

            # Mock Google Places API responses
            with respx.mock(base_url="https://maps.googleapis.com") as places_mock:
                geocode_response = {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "350 5th Ave, New York, NY 10118, USA",
                            "geometry": {
                                "location": {"lat": 40.7484405, "lng": -73.9856644}
                            },
                        }
                    ],
                }
                places_mock.get("/maps/api/geocode/json").mock(
                    return_value=httpx.Response(200, json=geocode_response)
                )

                with Bookalimo(
                    credentials=credentials, google_places_api_key="test-places-key"
                ) as client:
                    # Use Google Places to resolve pickup location
                    # Note: In real usage, you'd search for places first
                    pickup = Location(
                        type=LocationType.ADDRESS,
                        name="Empire State Building",
                        line1="350 5th Ave",
                        city="New York",
                        state="NY",
                        zip_code="10118",
                        country="US",
                        latitude=40.7484405,
                        longitude=-73.9856644,
                    )

                    dropoff = Location(
                        type=LocationType.AIRPORT,
                        name="LaGuardia Airport",
                        city="Queens",
                        state="NY",
                        country="US",
                        airport_code="LGA",
                    )

                    # Get quote using Places-resolved location
                    quote = client.pricing.quote(
                        rate_type=RateType.P2P,
                        date_time="09/30/2025 04:00 PM",
                        pickup=pickup,
                        dropoff=dropoff,
                        passengers=2,
                        luggage=2,
                    )

                    assert quote.token == "places-integration-token"
                    assert quote.total == 200.00

                    # Book using the quote
                    booking = client.reservations.book(
                        token=quote.token, credit_card=test_credit_card
                    )

                    assert booking.reservation_id == "RES_PLACES_123"
                    assert booking.success is True


@pytest.mark.integration
class TestRealWorldScenarios:
    """Tests for realistic usage scenarios."""

    @pytest.mark.asyncio
    async def test_business_trip_scenario(self, test_credit_card):
        """Test scenario: Business trip with multiple stops."""
        credentials = Credentials.create("business_user", "business_password")

        # Business trip: Hotel -> Meeting 1 -> Meeting 2 -> Airport
        locations = [
            Location(
                type=LocationType.ADDRESS,
                name="Business Hotel",
                line1="123 Business Blvd",
                city="New York",
                state="NY",
                country="US",
            ),
            Location(
                type=LocationType.ADDRESS,
                name="Corporate Office",
                line1="456 Corporate Way",
                city="New York",
                state="NY",
                country="US",
            ),
            Location(
                type=LocationType.ADDRESS,
                name="Client Office",
                line1="789 Client Street",
                city="New York",
                state="NY",
                country="US",
            ),
            Location(
                type=LocationType.AIRPORT,
                name="John F. Kennedy International Airport",
                city="Queens",
                state="NY",
                country="US",
                airport_code="JFK",
            ),
        ]

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Mock multiple quote responses for different legs
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "business-trip-token",
                        "total": 450.00,
                        "currency": "USD",
                        "car_class_code": "LUXURY",
                    },
                )
            )

            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "reservation_id": "RES_BUSINESS_001",
                        "confirmation": "CONF_BUSINESS_001",
                        "success": True,
                    },
                )
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Quote for multi-stop trip
                quote = await client.pricing.quote(
                    rate_type=RateType.HOURLY,
                    date_time="10/01/2025 08:00 AM",
                    pickup=locations[0],  # Hotel
                    dropoff=locations[3],  # Airport (final destination)
                    passengers=1,
                    luggage=1,
                    hours=6,  # Full day service
                    car_class_code="LUXURY",
                    customer_comment="Business trip with multiple stops. Driver should wait at each location.",
                )

                assert quote.total == 450.00
                assert quote.car_class_code == "LUXURY"

                # Book the trip
                booking = await client.reservations.book(
                    token=quote.token,
                    method="charge",  # Corporate account
                )

                assert booking.success is True
                assert "BUSINESS" in booking.confirmation

    def test_family_vacation_scenario(self, test_credit_card):
        """Test scenario: Family vacation with special requirements."""
        credentials = Credentials.create("family_user", "family_password")

        pickup = Location(
            type=LocationType.ADDRESS,
            name="Family Home",
            line1="789 Suburban Lane",
            city="New York",
            state="NY",
            country="US",
        )

        dropoff = Location(
            type=LocationType.AIRPORT,
            name="John F. Kennedy International Airport",
            city="Queens",
            state="NY",
            country="US",
            airport_code="JFK",
        )

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Initial quote
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "family-vacation-token",
                        "total": 125.00,
                        "currency": "USD",
                    },
                )
            )

            # Updated quote with car seats
            respx_mock.post("/booking/details/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "family-vacation-updated-token",
                        "total": 140.00,  # Additional fee for car seats
                        "currency": "USD",
                    },
                )
            )

            # Booking confirmation
            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "reservation_id": "RES_FAMILY_001",
                        "confirmation": "CONF_FAMILY_001",
                        "success": True,
                    },
                )
            )

            with Bookalimo(credentials=credentials) as client:
                # Initial quote for family trip
                quote = client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="12/20/2025 06:00 AM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=4,  # 2 adults, 2 children
                    luggage=4,  # Vacation luggage
                    customer_comment="Family vacation trip - early morning flight",
                )

                assert quote.total == 125.00

                # Update to add car seats for children
                updated_quote = client.pricing.update_details(
                    token=quote.token,
                    car_seats=2,  # 2 car seats for children
                    customer_comment="Family vacation trip - early morning flight. Need 2 car seats for children ages 3 and 5.",
                )

                assert updated_quote.total == 140.00  # Higher due to car seats

                # Book the family trip
                booking = client.reservations.book(
                    token=updated_quote.token,
                    credit_card=test_credit_card,
                    promo="FAMILY10",  # Family discount
                )

                assert booking.success is True
                assert "FAMILY" in booking.confirmation

    @pytest.mark.asyncio
    async def test_last_minute_booking_scenario(self, test_credit_card):
        """Test scenario: Last-minute urgent booking."""
        credentials = Credentials.create("urgent_user", "urgent_password")

        pickup = Location(
            type=LocationType.ADDRESS,
            name="Emergency Location",
            line1="Emergency Address",
            city="New York",
            state="NY",
            country="US",
        )

        dropoff = Location(
            type=LocationType.ADDRESS,
            name="Hospital",
            line1="Major Hospital",
            city="New York",
            state="NY",
            country="US",
        )

        with respx.mock(base_url="https://sandbox.bookalimo.com") as respx_mock:
            # Quick quote and booking for urgent situation
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "urgent-booking-token",
                        "total": 75.00,
                        "currency": "USD",
                    },
                )
            )

            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "reservation_id": "RES_URGENT_001",
                        "confirmation": "CONF_URGENT_001",
                        "success": True,
                    },
                )
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Very quick booking process
                import datetime

                now = datetime.datetime.now()
                booking_time = now.strftime("%m/%d/%Y %I:%M %p")

                quote = await client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time=booking_time,
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=0,
                    customer_comment="URGENT: Medical emergency transport needed ASAP",
                )

                # Immediate booking without details update
                booking = await client.reservations.book(
                    token=quote.token, credit_card=test_credit_card
                )

                assert booking.success is True
                assert "URGENT" in booking.confirmation
