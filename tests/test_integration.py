"""Integration tests for the Bookalimo SDK."""

import asyncio

import httpx
import pytest
import respx

from bookalimo import AsyncBookalimo, Bookalimo
from bookalimo.exceptions import BookalimoHTTPError, BookalimoTimeout
from bookalimo.schemas.booking import (
    Address,
    Airport,
    BookResponse,
    City,
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

from .conftest import TEST_BASE_URL


@pytest.mark.integration
class TestEndToEndBookingFlow:
    """Test complete booking flows from start to finish."""

    @pytest.fixture
    def booking_locations(self):
        """Sample locations for booking flow tests."""
        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="123 Business Ave",
                street_name="123 Business Ave",
                suite="Suite 100",
                zip="10001",
                city=City(
                    city_name="New York",
                    country_code="US",
                    state_code="NY",
                    state_name="New York",
                ),
            ),
        )

        dropoff = Location(
            type=LocationType.AIRPORT,
            airport=Airport(iata_code="JFK", country_code="US", state_code="NY"),
        )

        return pickup, dropoff

    @pytest.mark.asyncio
    async def test_complete_async_booking_flow(
        self, booking_locations, test_credit_card
    ):
        """Test complete async booking flow: quote -> update -> book."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create("integration_user", "integration_password")

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Mock quote response
            quote_response = {
                "token": "integration-token-12345",
                "prices": [
                    {
                        "car_class": "SEDAN",
                        "car_description": "Standard Sedan",
                        "max_passengers": 4,
                        "max_luggage": 4,
                        "price": 175.50,
                        "price_default": 175.50,
                        "image128": "sedan_128.jpg",
                        "image256": "sedan_256.jpg",
                        "image512": "sedan_512.jpg",
                        "meet_greets": [],
                    }
                ],
            }
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            # Mock details update response
            details_response = {
                "price": 225.50,
                "breakdown": [
                    {"name": "Base Rate", "value": 200.00, "is_grand": False},
                    {"name": "Tax", "value": 12.50, "is_grand": False},
                    {"name": "Tip", "value": 13.00, "is_grand": False},
                    {"name": "Total", "value": 225.50, "is_grand": True},
                ],
            }
            respx_mock.post("/booking/details/").mock(
                return_value=httpx.Response(200, json=details_response)
            )

            # Mock booking response
            book_response = {"reservation_id": "RES_INTEGRATION_123"}
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
                assert len(quote.prices) > 0
                assert quote.prices[0].price == 175.50
                assert quote.prices[0].car_class == "SEDAN"

                # Step 2: Update details (upgrade car class)
                updated_details = await client.pricing.update_details(
                    token=quote.token,
                    car_class_code="SUV",
                    customer_comment="Upgraded to SUV, please arrive 10 minutes early",
                )

                assert isinstance(updated_details, DetailsResponse)
                assert updated_details.price == 225.50
                assert len(updated_details.breakdown) > 0
                # Check that total is in breakdown
                total_breakdown = next(
                    (item for item in updated_details.breakdown if item.is_grand), None
                )
                assert total_breakdown is not None
                assert total_breakdown.value == 225.50

                # Step 3: Book the reservation
                booking = await client.reservations.book(
                    token=quote.token, credit_card=test_credit_card
                )

                assert isinstance(booking, BookResponse)
                assert booking.reservation_id == "RES_INTEGRATION_123"

    def test_complete_sync_booking_flow(self, booking_locations, test_credit_card):
        """Test complete sync booking flow: quote -> book with charge method."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create(
            "sync_integration_user", "sync_integration_password"
        )

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Mock quote response
            quote_response = {
                "token": "sync-integration-token-98765",
                "prices": [
                    {
                        "car_class": "SEDAN",
                        "car_description": "Standard Sedan",
                        "max_passengers": 4,
                        "max_luggage": 4,
                        "price": 150.00,
                        "price_default": 150.00,
                        "image128": "sedan_128.jpg",
                        "image256": "sedan_256.jpg",
                        "image512": "sedan_512.jpg",
                        "meet_greets": [],
                    }
                ],
            }
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            # Mock booking response (charge account)
            book_response = {"reservation_id": "RES_SYNC_INTEGRATION_789"}
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
                assert len(quote.prices) > 0
                assert quote.prices[0].price == 150.00

                # Step 2: Book with charge method (corporate account)
                booking = client.reservations.book(token=quote.token, method="charge")

                assert booking.reservation_id == "RES_SYNC_INTEGRATION_789"

    @pytest.mark.asyncio
    async def test_reservation_management_flow(self):
        """Test complete reservation management flow: list -> get -> edit."""
        credentials = Credentials.create(
            "reservation_mgmt_user", "reservation_mgmt_password"
        )

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Mock list reservations response
            list_response = {
                "success": True,
                "reservations": [
                    {
                        "confirmation_number": "CONF_MGR_001",
                        "is_archive": False,
                        "local_date_time": "09/15/2025 03:00 PM",
                        "rate_type": 0,
                        "passenger_name": "John Doe",
                        "pickup_type": 0,
                        "pickup": "123 Business Ave, New York, NY",
                        "dropoff_type": 1,
                        "dropoff": "JFK Airport, Queens, NY",
                        "car_class": "SEDAN",
                        "status": None,
                    },
                    {
                        "confirmation_number": "CONF_MGR_002",
                        "is_archive": False,
                        "local_date_time": "09/16/2025 10:00 AM",
                        "rate_type": 0,
                        "passenger_name": "Jane Smith",
                        "pickup_type": 0,
                        "pickup": "456 Client Street, New York, NY",
                        "dropoff_type": 1,
                        "dropoff": "LGA Airport, Queens, NY",
                        "car_class": "SUV",
                        "status": None,
                    },
                ],
            }
            respx_mock.post("/booking/reservation/list/").mock(
                return_value=httpx.Response(200, json=list_response)
            )

            # Mock get reservation response
            get_response = {
                "reservation": {
                    "confirmation": "CONF_MGR_001",
                    "is_cancel_request": False,
                    "passengers": 2,
                    "luggage": 2,
                },
                "is_editable": True,
                "status": None,
                "is_cancellation_pending": False,
                "car_description": "Standard Sedan",
                "pickup_type": 0,
                "pickup_description": "123 Business Ave, New York, NY",
                "dropoff_type": 1,
                "dropoff_description": "JFK Airport, Queens, NY",
                "passenger_name": "John Doe",
                "breakdown": [{"name": "Total", "value": 175.50, "is_grand": True}],
            }
            respx_mock.post("/booking/reservation/get/").mock(
                return_value=httpx.Response(200, json=get_response)
            )

            # Mock edit reservation response
            edit_response = {"success": True}
            respx_mock.post("/booking/edit/").mock(
                return_value=httpx.Response(200, json=edit_response)
            )

            async with AsyncBookalimo(credentials=credentials) as client:
                # Step 1: List active reservations
                reservations = await client.reservations.list()

                assert isinstance(reservations, ListReservationsResponse)
                assert reservations.success is True
                assert len(reservations.reservations) == 2

                # Step 2: Get details of first reservation
                reservation_details = await client.reservations.get("CONF_MGR_001")

                assert isinstance(reservation_details, GetReservationResponse)
                assert reservation_details.reservation.confirmation == "CONF_MGR_001"
                assert reservation_details.is_editable is True
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

    @pytest.mark.asyncio
    async def test_error_handling_throughout_flow(self, booking_locations):
        """Test error handling at different stages of booking flow."""
        pickup, dropoff = booking_locations
        credentials = Credentials.create("error_test_user", "error_test_password")

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Mock quote request that succeeds
            quote_response = {
                "token": "error-test-token-123",
                "prices": [
                    {
                        "car_class": "SEDAN",
                        "car_description": "Standard Sedan",
                        "max_passengers": 4,
                        "max_luggage": 4,
                        "price": 100.00,
                        "price_default": 100.00,
                        "image128": "sedan_128.jpg",
                        "image256": "sedan_256.jpg",
                        "image512": "sedan_512.jpg",
                        "meet_greets": [],
                    }
                ],
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

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
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

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Mock different responses for different requests
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "concurrent-token",
                        "prices": [
                            {
                                "car_class": "SEDAN",
                                "car_description": "Standard Sedan",
                                "max_passengers": 4,
                                "max_luggage": 4,
                                "price": 150.00,
                                "price_default": 150.00,
                                "image128": "sedan_128.jpg",
                                "image256": "sedan_256.jpg",
                                "image512": "sedan_512.jpg",
                                "meet_greets": [],
                            }
                        ],
                    },
                )
            )

            respx_mock.post("/booking/reservation/list/").mock(
                return_value=httpx.Response(
                    200, json={"success": True, "reservations": []}
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
                assert list_result.success is True
                assert len(list_result.reservations) == 0


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

        with respx.mock(base_url=TEST_BASE_URL) as booking_mock:
            # Mock booking API responses
            quote_response = {
                "token": "places-integration-token",
                "prices": [
                    {
                        "car_class": "SEDAN",
                        "car_description": "Standard Sedan",
                        "max_passengers": 4,
                        "max_luggage": 4,
                        "price": 200.00,
                        "price_default": 200.00,
                        "image128": "sedan_128.jpg",
                        "image256": "sedan_256.jpg",
                        "image512": "sedan_512.jpg",
                        "meet_greets": [],
                    }
                ],
            }
            booking_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=quote_response)
            )

            book_response = {"reservation_id": "RES_PLACES_123"}
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
                    from bookalimo.schemas.places.google import GeocodingRequest

                    # Geocode the address using Google Places
                    geocode_request = GeocodingRequest(
                        address="350 5th Ave, New York, NY 10118, USA"
                    )
                    geocode_result = client.places.geocode(geocode_request)

                    # Create location from geocoded result
                    pickup = Location(
                        type=LocationType.ADDRESS,
                        address=Address(
                            google_geocode=geocode_result,
                            street_name="350 5th Ave",
                        ),
                    )

                    dropoff = Location(
                        type=LocationType.AIRPORT,
                        airport=Airport(
                            iata_code="LGA", country_code="US", state_code="NY"
                        ),
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
                    assert len(quote.prices) > 0
                    assert quote.prices[0].price == 200.00

                    # Book using the quote
                    booking = client.reservations.book(
                        token=quote.token, credit_card=test_credit_card
                    )

                    assert booking.reservation_id == "RES_PLACES_123"


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
                address=Address(
                    place_name="Business Hotel",
                    street_name="123 Business Blvd",
                    city=City(
                        city_name="New York",
                        country_code="US",
                        state_code="NY",
                        state_name="New York",
                    ),
                ),
            ),
            Location(
                type=LocationType.ADDRESS,
                address=Address(
                    place_name="Corporate Office",
                    street_name="456 Corporate Way",
                    city=City(
                        city_name="New York",
                        country_code="US",
                        state_code="NY",
                        state_name="New York",
                    ),
                ),
            ),
            Location(
                type=LocationType.ADDRESS,
                address=Address(
                    place_name="Client Office",
                    street_name="789 Client Street",
                    city=City(
                        city_name="New York",
                        country_code="US",
                        state_code="NY",
                        state_name="New York",
                    ),
                ),
            ),
            Location(
                type=LocationType.AIRPORT,
                airport=Airport(iata_code="JFK", country_code="US", state_code="NY"),
            ),
        ]

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Mock multiple quote responses for different legs
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "business-trip-token",
                        "prices": [
                            {
                                "car_class": "LUXURY",
                                "car_description": "Luxury Vehicle",
                                "max_passengers": 4,
                                "max_luggage": 4,
                                "price": 450.00,
                                "price_default": 450.00,
                                "image128": "luxury_128.jpg",
                                "image256": "luxury_256.jpg",
                                "image512": "luxury_512.jpg",
                                "meet_greets": [],
                            }
                        ],
                    },
                )
            )

            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(
                    200,
                    json={"reservation_id": "RES_BUSINESS_001"},
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

                assert len(quote.prices) > 0
                assert quote.prices[0].price == 450.00
                assert quote.prices[0].car_class == "LUXURY"

                # Book the trip
                booking = await client.reservations.book(
                    token=quote.token,
                    method="charge",  # Corporate account
                )

                assert booking.reservation_id == "RES_BUSINESS_001"

    def test_family_vacation_scenario(self, test_credit_card):
        """Test scenario: Family vacation with special requirements."""
        credentials = Credentials.create("family_user", "family_password")

        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="Family Home",
                street_name="789 Suburban Lane",
                city=City(
                    city_name="New York",
                    country_code="US",
                    state_code="NY",
                    state_name="New York",
                ),
            ),
        )

        dropoff = Location(
            type=LocationType.AIRPORT,
            airport=Airport(iata_code="JFK", country_code="US", state_code="NY"),
        )

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Initial quote
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "family-vacation-token",
                        "prices": [
                            {
                                "car_class": "SEDAN",
                                "car_description": "Standard Sedan",
                                "max_passengers": 4,
                                "max_luggage": 4,
                                "price": 125.00,
                                "price_default": 125.00,
                                "image128": "sedan_128.jpg",
                                "image256": "sedan_256.jpg",
                                "image512": "sedan_512.jpg",
                                "meet_greets": [],
                            }
                        ],
                    },
                )
            )

            # Updated quote with car seats
            respx_mock.post("/booking/details/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "price": 140.00,  # Additional fee for car seats
                        "breakdown": [
                            {"name": "Base Rate", "value": 125.00, "is_grand": False},
                            {"name": "Car Seats", "value": 15.00, "is_grand": False},
                            {"name": "Total", "value": 140.00, "is_grand": True},
                        ],
                    },
                )
            )

            # Booking confirmation
            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(
                    200,
                    json={"reservation_id": "RES_FAMILY_001"},
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

                assert len(quote.prices) > 0
                assert quote.prices[0].price == 125.00

                # Update to add car seats for children
                updated_quote = client.pricing.update_details(
                    token=quote.token,
                    car_seats=2,  # 2 car seats for children
                    customer_comment="Family vacation trip - early morning flight. Need 2 car seats for children ages 3 and 5.",
                )

                assert updated_quote.price == 140.00  # Higher due to car seats

                # Book the family trip
                booking = client.reservations.book(
                    token=quote.token,
                    credit_card=test_credit_card,
                    promo="FAMILY10",  # Family discount
                )

                assert booking.reservation_id == "RES_FAMILY_001"

    @pytest.mark.asyncio
    async def test_last_minute_booking_scenario(self, test_credit_card):
        """Test scenario: Last-minute urgent booking."""
        credentials = Credentials.create("urgent_user", "urgent_password")

        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="Emergency Location",
                street_name="Emergency Address",
                city=City(
                    city_name="New York",
                    country_code="US",
                    state_code="NY",
                    state_name="New York",
                ),
            ),
        )

        dropoff = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="Hospital",
                street_name="Major Hospital",
                city=City(
                    city_name="New York",
                    country_code="US",
                    state_code="NY",
                    state_name="New York",
                ),
            ),
        )

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            # Quick quote and booking for urgent situation
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "token": "urgent-booking-token",
                        "prices": [
                            {
                                "car_class": "SEDAN",
                                "car_description": "Standard Sedan",
                                "max_passengers": 4,
                                "max_luggage": 4,
                                "price": 75.00,
                                "price_default": 75.00,
                                "image128": "sedan_128.jpg",
                                "image256": "sedan_256.jpg",
                                "image512": "sedan_512.jpg",
                                "meet_greets": [],
                            }
                        ],
                    },
                )
            )

            respx_mock.post("/booking/book/").mock(
                return_value=httpx.Response(
                    200,
                    json={"reservation_id": "RES_URGENT_001"},
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

                assert booking.reservation_id == "RES_URGENT_001"
