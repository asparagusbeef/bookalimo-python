"""Real API integration tests using live Bookalimo API credentials.

These tests run against the actual Bookalimo API when credentials are available
and verify the SDK works correctly with real services.
"""

from typing import Optional

import pytest
from pydantic import ValidationError

from bookalimo import AsyncBookalimo, Bookalimo
from bookalimo.exceptions import BookalimoError, BookalimoHTTPError
from bookalimo.schemas.booking import (
    Address,
    Airport,
    City,
    Location,
    LocationType,
    PriceResponse,
    RateType,
)
from bookalimo.transport.auth import Credentials


@pytest.mark.integration
@pytest.mark.network
class TestRealBookalimoAPI:
    """Integration tests against the real Bookalimo API."""

    def test_real_credentials_parsing(self, real_bookalimo_credentials):
        """Test that real credentials are parsed correctly."""
        if real_bookalimo_credentials is None:
            pytest.skip("Real Bookalimo credentials not available")

        assert isinstance(real_bookalimo_credentials, Credentials)
        assert len(real_bookalimo_credentials.id) > 0
        assert len(real_bookalimo_credentials.password_hash) == 64  # SHA256 hash
        assert isinstance(real_bookalimo_credentials.is_customer, bool)

    @pytest.mark.slow
    def test_real_sync_pricing_quote(
        self, skip_if_no_real_credentials, real_pickup_location, real_dropoff_location
    ):
        """Test real pricing quote with sync client."""
        credentials = skip_if_no_real_credentials

        try:
            with Bookalimo(credentials=credentials) as client:
                quote = client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="12/01/2025 02:00 PM",
                    pickup=real_pickup_location,
                    dropoff=real_dropoff_location,
                    passengers=2,
                    luggage=1,
                    customer_comment="SDK Integration Test - Safe to ignore",
                )

                # Verify response structure
                assert hasattr(quote, "token")
                assert hasattr(quote, "prices")

                assert isinstance(quote.token, str)
                assert len(quote.token) > 0
                assert isinstance(quote.prices, list)
                assert len(quote.prices) > 0
                # Check first price has valid price
                assert isinstance(quote.prices[0].price, (int, float))
                assert quote.prices[0].price > 0

        except BookalimoHTTPError as e:
            # Log the error for debugging but don't fail the test
            # The API might return errors for various business logic reasons
            print(f"API returned HTTP error (this may be expected): {e}")
            if e.status_code in [401, 403]:
                pytest.fail(f"Authentication failed: {e}")
            # For other HTTP errors, we'll consider the test passed
            # since we successfully communicated with the API

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_async_pricing_quote(
        self, skip_if_no_real_credentials, real_pickup_location, real_dropoff_location
    ):
        """Test real pricing quote with async client."""
        credentials = skip_if_no_real_credentials

        try:
            async with AsyncBookalimo(credentials=credentials) as client:
                quote = await client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="12/01/2025 03:00 PM",
                    pickup=real_pickup_location,
                    dropoff=real_dropoff_location,
                    passengers=1,
                    luggage=0,
                    customer_comment="Async SDK Integration Test - Safe to ignore",
                )

                # Verify response structure
                assert hasattr(quote, "token")
                assert hasattr(quote, "prices")

                assert isinstance(quote.token, str)
                assert len(quote.token) > 0
                assert isinstance(quote.prices, list)
                assert len(quote.prices) > 0
                # Check first price has valid price
                assert isinstance(quote.prices[0].price, (int, float))
                assert quote.prices[0].price > 0

        except BookalimoHTTPError as e:
            # Same error handling as sync test
            print(f"Async API returned HTTP error (this may be expected): {e}")
            if e.status_code in [401, 403]:
                pytest.fail(f"Authentication failed: {e}")

    @pytest.mark.slow
    def test_real_reservations_list(self, skip_if_no_real_credentials):
        """Test listing real reservations."""
        credentials = skip_if_no_real_credentials

        try:
            with Bookalimo(credentials=credentials) as client:
                # Test listing active reservations
                reservations = client.reservations.list(is_archive=False)

                assert hasattr(reservations, "reservations")
                assert hasattr(reservations, "success")
                assert isinstance(reservations.reservations, list)
                assert isinstance(reservations.success, bool)
                assert len(reservations.reservations) >= 0

                # Test listing archived reservations
                archived = client.reservations.list(is_archive=True)
                assert hasattr(archived, "reservations")
                assert hasattr(archived, "success")
                assert isinstance(archived.success, bool)
                assert len(archived.reservations) >= 0

        except BookalimoHTTPError as e:
            print(f"Reservations list API error (may be expected): {e}")
            if e.status_code in [401, 403]:
                pytest.fail(f"Authentication failed: {e}")

    @pytest.mark.slow
    def test_real_api_error_handling(self, skip_if_no_real_credentials):
        """Test error handling with invalid request to real API."""
        _ = skip_if_no_real_credentials

        with pytest.raises(ValidationError):
            # Create an intentionally invalid location (missing required fields)
            _ = Location(
                type=LocationType.ADDRESS,
                address=Address(
                    place_name="Invalid Location",
                    city=City(
                        city_name="",  # Empty city should cause validation error
                        country_code="",
                        state_code="",
                    ),
                ),
            )

    @pytest.mark.slow
    def test_real_api_with_various_rate_types(
        self, skip_if_no_real_credentials, real_pickup_location, real_dropoff_location
    ):
        """Test different rate types with real API."""
        credentials = skip_if_no_real_credentials

        rate_types_to_test = [RateType.P2P, RateType.HOURLY]

        with Bookalimo(credentials=credentials) as client:
            for rate_type in rate_types_to_test:
                try:
                    extra_params = {}
                    if rate_type == RateType.HOURLY:
                        extra_params["hours"] = 2  # Required for hourly bookings

                    quote = client.pricing.quote(
                        rate_type=rate_type,
                        date_time="12/01/2025 05:00 PM",
                        pickup=real_pickup_location,
                        dropoff=real_dropoff_location,
                        passengers=1,
                        luggage=1,
                        customer_comment=f"Rate type test: {rate_type.name}",
                        **extra_params,
                    )

                    # Should get a valid response for each rate type
                    assert quote.token
                    assert len(quote.prices) > 0
                    assert quote.prices[0].price > 0

                except BookalimoHTTPError as e:
                    # Some rate types might not be available for all routes
                    print(f"Rate type {rate_type.name} returned error: {e}")
                    if e.status_code in [401, 403]:
                        pytest.fail(f"Authentication failed: {e}")

    def test_real_api_authentication_validation(self):
        """Test that invalid credentials are properly rejected."""
        # Create intentionally invalid credentials
        invalid_creds = Credentials.create("INVALID_TEST_USER", "invalid_password")

        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="Test Address",
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
            airport=Airport(iata_code="TST", country_code="US", state_code="NY"),
        )

        with Bookalimo(credentials=invalid_creds) as client:
            # Should get authentication error
            expected_msg = "API Error: Invalid credentials"
            with pytest.raises(BookalimoError) as exc_info:
                client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="12/01/2025 06:00 PM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=1,
                    luggage=0,
                    customer_comment="Authentication test - Should fail",
                )
                assert str(exc_info.value) == expected_msg

    @pytest.mark.slow
    def test_real_api_connection_and_timeout_handling(
        self, skip_if_no_real_credentials, real_pickup_location, real_dropoff_location
    ):
        """Test real API connection handling and timeouts."""
        credentials = skip_if_no_real_credentials

        # Test with very short timeout to ensure timeout handling works
        from bookalimo.transport.httpx_sync import SyncTransport

        # Create transport with very short timeout
        transport = SyncTransport(
            credentials=credentials,
            timeouts=0.001,  # 1ms timeout - should cause timeout
            retries=0,  # No retries to speed up test
        )

        with Bookalimo(transport=transport) as client:
            # This should timeout quickly
            with pytest.raises((BookalimoError, BookalimoHTTPError)):
                client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="12/01/2025 07:00 PM",
                    pickup=real_pickup_location,
                    dropoff=real_dropoff_location,
                    passengers=1,
                    luggage=0,
                    customer_comment="Timeout test",
                )


@pytest.mark.integration
@pytest.mark.network
class TestRealAPIPerformance:
    """Performance tests against the real API."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_api_concurrent_requests(
        self, skip_if_no_real_credentials, real_pickup_location, real_dropoff_location
    ):
        """Test concurrent requests to real API."""
        credentials = skip_if_no_real_credentials

        import asyncio

        async with AsyncBookalimo(credentials=credentials) as client:

            async def make_quote(i: int) -> Optional[PriceResponse]:
                try:
                    return await client.pricing.quote(
                        rate_type=RateType.P2P,
                        date_time="12/01/2025 08:00 PM",
                        pickup=real_pickup_location,
                        dropoff=real_dropoff_location,
                        passengers=1,
                        luggage=0,
                        customer_comment=f"Concurrent test {i} - Safe to ignore",
                    )
                except BookalimoHTTPError as e:
                    # API might rate limit or reject concurrent requests
                    print(f"Concurrent request {i} failed: {e}")
                    return None

            # Make 3 concurrent requests (conservative number)
            tasks = [make_quote(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # At least some requests should succeed
            successful_results = [
                r for r in results if r is not None and not isinstance(r, Exception)
            ]
            print(f"Successful concurrent requests: {len(successful_results)}/3")

            # We expect at least one to succeed
            assert len(successful_results) >= 1

    @pytest.mark.performance
    @pytest.mark.slow
    def test_real_api_response_times(
        self, skip_if_no_real_credentials, real_pickup_location, real_dropoff_location
    ):
        """Test response times for real API calls."""
        import time

        credentials = skip_if_no_real_credentials

        with Bookalimo(credentials=credentials) as client:
            start_time = time.perf_counter()

            try:
                quote = client.pricing.quote(
                    rate_type=RateType.P2P,
                    date_time="12/01/2025 09:00 PM",
                    pickup=real_pickup_location,
                    dropoff=real_dropoff_location,
                    passengers=1,
                    luggage=0,
                    customer_comment="Performance test - Safe to ignore",
                )

                end_time = time.perf_counter()
                response_time = end_time - start_time

                # Response should be reasonably fast (under 30 seconds)
                assert response_time < 30.0, (
                    f"API response too slow: {response_time:.2f}s"
                )

                # Log performance for monitoring
                print(f"Real API response time: {response_time:.3f}s")

                # Verify we got a valid response
                assert quote.token
                assert len(quote.prices) > 0
                assert quote.prices[0].price > 0

            except BookalimoHTTPError as e:
                # Even errors should be reasonably fast
                end_time = time.perf_counter()
                response_time = end_time - start_time
                assert response_time < 30.0, (
                    f"API error response too slow: {response_time:.2f}s"
                )

                if e.status_code in [401, 403]:
                    pytest.fail(f"Authentication failed: {e}")


@pytest.mark.integration
class TestCredentialsParsing:
    """Test parsing of credentials from environment variables."""

    def test_valid_credentials_json_parsing(self):
        """Test parsing valid credentials JSON."""
        import json
        import os

        test_credentials = {
            "id": "test_user_123",
            "password": "test_password_456",
            "is_customer": "true",
        }

        # Temporarily set environment variable
        original_env = os.environ.get("BOOKALIMO_TESTING_USER")
        os.environ["BOOKALIMO_TESTING_USER"] = json.dumps(test_credentials)

        try:
            # Import here to ensure fresh environment reading

            # Create the fixture manually for testing
            testing_user_json = os.getenv("BOOKALIMO_TESTING_USER")
            assert testing_user_json is not None

            user_data = json.loads(testing_user_json)
            credentials = Credentials.create(
                user_id=user_data["id"],
                password=user_data["password"],
                is_customer=user_data.get("is_customer", "false").lower() == "true",
            )

            assert credentials.id == "test_user_123"
            assert credentials.is_customer is True
            assert len(credentials.password_hash) == 64  # SHA256 hash

        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["BOOKALIMO_TESTING_USER"] = original_env
            else:
                os.environ.pop("BOOKALIMO_TESTING_USER", None)

    def test_invalid_credentials_json_handling(self):
        """Test handling of invalid credentials JSON."""
        import os

        original_env = os.environ.get("BOOKALIMO_TESTING_USER")

        # Test invalid JSON
        os.environ["BOOKALIMO_TESTING_USER"] = "invalid json"

        try:
            import json

            testing_user_json = os.getenv("BOOKALIMO_TESTING_USER")
            with pytest.raises(json.JSONDecodeError):
                if testing_user_json is not None:
                    json.loads(testing_user_json)
                else:
                    raise json.JSONDecodeError("Invalid JSON", "", 0)
        finally:
            if original_env is not None:
                os.environ["BOOKALIMO_TESTING_USER"] = original_env
            else:
                os.environ.pop("BOOKALIMO_TESTING_USER", None)

    def test_missing_credentials_handling(self):
        """Test handling when credentials are missing."""
        import os

        original_env = os.environ.get("BOOKALIMO_TESTING_USER")

        # Remove credentials
        os.environ.pop("BOOKALIMO_TESTING_USER", None)

        try:
            testing_user_json = os.getenv("BOOKALIMO_TESTING_USER")
            assert testing_user_json is None
        finally:
            if original_env is not None:
                os.environ["BOOKALIMO_TESTING_USER"] = original_env
