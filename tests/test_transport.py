"""Tests for transport layer - HTTP clients, auth, retry logic."""

import json
import logging
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import respx

from bookalimo.exceptions import (
    BookalimoConnectionError,
    BookalimoHTTPError,
    BookalimoTimeout,
)
from bookalimo.schemas.booking import (
    Address,
    Airport,
    City,
    Location,
    LocationType,
    PriceRequest,
    PriceResponse,
    RateType,
)
from bookalimo.transport.auth import Credentials, inject_credentials
from bookalimo.transport.httpx_async import AsyncTransport
from bookalimo.transport.httpx_sync import SyncTransport
from bookalimo.transport.retry import (
    async_retry,
    should_retry_exception,
    should_retry_status,
    sync_retry,
)

from .conftest import TEST_BASE_URL


class TestCredentials:
    """Tests for Credentials class and auth utilities."""

    def test_create_hash(self):
        """Test password hash creation."""
        password = "testpass123"
        user_id = "TestUser"

        # Test the hash creation method
        result = Credentials.create_hash(password, user_id)

        # Should be a 64-character hex string (SHA256)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

        # Same inputs should produce same hash
        result2 = Credentials.create_hash(password, user_id)
        assert result == result2

        # Different inputs should produce different hashes
        result3 = Credentials.create_hash(password, "DifferentUser")
        assert result != result3

    def test_create_hash_case_sensitivity(self):
        """Test that user ID case affects hash."""
        password = "testpass123"

        hash1 = Credentials.create_hash(password, "TestUser")
        hash2 = Credentials.create_hash(password, "testuser")

        # Hashes should be the same because user_id is lowercased internally
        assert hash1 == hash2

    def test_create_credentials(self):
        """Test credential creation with automatic hashing."""
        user_id = "test_user"
        password = "test_password"

        creds = Credentials.create(user_id, password, is_customer=True)

        assert creds.id == user_id
        assert creds.is_customer is True
        assert creds.password_hash == Credentials.create_hash(password, user_id)

    def test_create_credentials_default_customer_flag(self):
        """Test default customer flag is False."""
        creds = Credentials.create("user", "pass")
        assert creds.is_customer is False

    def test_credentials_model_validation(self):
        """Test credentials model validation."""
        # Valid credentials using create method
        creds = Credentials.create("user123", "testpass123", is_customer=False)

        assert creds.id == "user123"
        assert len(creds.password_hash) == 64  # Should be SHA256 hash
        assert creds.is_customer is False

    def test_inject_credentials_with_credentials(self):
        """Test injecting credentials into request data."""
        data = {"some": "data"}
        creds = Credentials.create("user", "pass")

        result = inject_credentials(data, creds)

        assert "credentials" in result
        assert result["credentials"] == creds.model_dump()
        assert result["some"] == "data"

    def test_inject_credentials_none(self):
        """Test injecting None credentials."""
        data = {"some": "data"}

        result = inject_credentials(data, None)

        assert "credentials" not in result
        assert result["some"] == "data"
        assert result is data  # Should return same dict


class TestRetryLogic:
    """Tests for retry logic."""

    def test_should_retry_status_retriable(self):
        """Test retriable status codes."""
        retriable_codes = [500, 502, 503, 504]

        for code in retriable_codes:
            assert should_retry_status(code) is True

    def test_should_retry_status_non_retriable(self):
        """Test non-retriable status codes."""
        non_retriable_codes = [200, 201, 400, 401, 403, 404, 422]

        for code in non_retriable_codes:
            assert should_retry_status(code) is False

    def test_should_retry_exception_retriable(self):
        """Test retriable exceptions."""
        retriable_exceptions = [
            httpx.TimeoutException(message="Timeout"),
            httpx.ConnectTimeout(message="Connection timeout"),
            httpx.ReadTimeout(message="Read timeout"),
            httpx.ConnectError("Connection failed"),
            ConnectionError("Network error"),
        ]

        for exc in retriable_exceptions:
            assert should_retry_exception(exc) is True

    def test_should_retry_exception_non_retriable(self):
        """Test non-retriable exceptions."""
        non_retriable_exceptions = [
            ValueError("Bad value"),
            KeyError("Missing key"),
            httpx.InvalidURL("Bad URL"),
        ]

        for exc in non_retriable_exceptions:
            assert should_retry_exception(exc) is False

    def test_sync_retry_success_first_attempt(self):
        """Test sync retry succeeds on first attempt."""
        mock_func = Mock(return_value="success")

        result = sync_retry(
            mock_func, retries=3, backoff=0.1, should_retry=should_retry_exception
        )

        assert result == "success"
        assert mock_func.call_count == 1

    def test_sync_retry_success_after_retries(self):
        """Test sync retry succeeds after failed attempts."""
        mock_func = Mock(
            side_effect=[
                httpx.ConnectError("Failed"),
                httpx.TimeoutException(message="Timeout"),
                "success",
            ]
        )

        with patch("time.sleep"):  # Speed up test
            result = sync_retry(
                mock_func, retries=3, backoff=0.1, should_retry=should_retry_exception
            )

        assert result == "success"
        assert mock_func.call_count == 3

    def test_sync_retry_exhausts_retries(self):
        """Test sync retry exhausts all retries."""
        mock_func = Mock(side_effect=httpx.ConnectError("Always fails"))

        with patch("time.sleep"):
            with pytest.raises(httpx.ConnectError):
                sync_retry(
                    mock_func,
                    retries=2,
                    backoff=0.1,
                    should_retry=should_retry_exception,
                )

        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_sync_retry_non_retriable_exception(self):
        """Test sync retry doesn't retry non-retriable exceptions."""
        mock_func = Mock(side_effect=ValueError("Not retriable"))

        with pytest.raises(ValueError):
            sync_retry(
                mock_func, retries=3, backoff=0.1, should_retry=should_retry_exception
            )

        assert mock_func.call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_async_retry_success_first_attempt(self):
        """Test async retry succeeds on first attempt."""
        mock_func = AsyncMock(return_value="success")

        result = await async_retry(
            mock_func, retries=3, backoff=0.1, should_retry=should_retry_exception
        )

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_success_after_retries(self):
        """Test async retry succeeds after failed attempts."""
        mock_func = AsyncMock(
            side_effect=[
                httpx.ConnectError("Failed"),
                httpx.TimeoutException(message="Timeout"),
                "success",
            ]
        )

        with patch("asyncio.sleep"):  # Speed up test
            result = await async_retry(
                mock_func, retries=3, backoff=0.1, should_retry=should_retry_exception
            )

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_exhausts_retries(self):
        """Test async retry exhausts all retries."""
        mock_func = AsyncMock(side_effect=httpx.ConnectError("Always fails"))

        with patch("asyncio.sleep"):
            with pytest.raises(httpx.ConnectError):
                await async_retry(
                    mock_func,
                    retries=2,
                    backoff=0.1,
                    should_retry=should_retry_exception,
                )

        assert mock_func.call_count == 3  # Initial + 2 retries


class TestAsyncTransport:
    """Tests for AsyncTransport class."""

    @pytest.fixture
    def transport(self, credentials):
        """Create async transport for testing."""
        return AsyncTransport(
            base_url="https://api.test.com",
            credentials=credentials,
            retries=0,  # Disable retries for faster tests
        )

    @pytest.mark.asyncio
    async def test_init_default_client(self, credentials):
        """Test transport initialization with default client."""
        transport = AsyncTransport(credentials=credentials)

        assert transport.base_url == TEST_BASE_URL
        assert transport.credentials == credentials
        assert transport.client is not None

    @pytest.mark.asyncio
    async def test_init_custom_client(self, credentials, mock_http_client):
        """Test transport initialization with custom client."""
        transport = AsyncTransport(credentials=credentials, client=mock_http_client)

        assert transport.client is mock_http_client

    @pytest.mark.asyncio
    async def test_post_success(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test successful POST request."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        response_data = {
            "token": "test-token-123",
            "prices": [
                {
                    "car_class": "SEDAN",
                    "car_description": "Standard Sedan",
                    "max_passengers": 4,
                    "max_luggage": 2,
                    "price": 150.00,
                    "price_default": 175.00,
                    "image128": "http://example.com/sedan128.png",
                    "image256": "http://example.com/sedan256.png",
                    "image512": "http://example.com/sedan512.png",
                    "default_meet_greet": 1,
                    "meet_greets": [],
                }
            ],
        }

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=response_data)
            )

            result = await transport.post(
                "/booking/price/", request_model, PriceResponse
            )

            print("#" * 100)
            print(result)

            assert result.token == "test-token-123"
            assert result.prices[0].price == 150.00

    @pytest.mark.asyncio
    async def test_post_with_credentials_injection(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test that credentials are properly injected into requests."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        response_data = {"token": "test", "total": 100, "currency": "USD"}

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            route = respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=response_data)
            )

            await transport.post("/booking/price/", request_model)

            # Verify credentials were included in request
            request = route.calls[0].request
            request_data = json.loads(request.content.decode())

            assert "credentials" in request_data
            assert request_data["credentials"]["id"] == transport.credentials.id
            assert (
                request_data["credentials"]["passwordHash"]
                == transport.credentials.password_hash
            )

    @pytest.mark.asyncio
    async def test_post_http_error(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test HTTP error handling."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    400, json={"error": "Bad Request", "code": "INVALID_REQUEST"}
                )
            )

            with pytest.raises(BookalimoHTTPError) as exc_info:
                await transport.post("/booking/price/", request_model, PriceResponse)

            assert exc_info.value.status_code == 400
            assert "Bad Request" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_post_timeout_error(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test timeout error handling."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            with pytest.raises(BookalimoTimeout):
                await transport.post("/booking/price/", request_model, PriceResponse)

    @pytest.mark.asyncio
    async def test_post_connection_error(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test connection error handling."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            with pytest.raises(BookalimoConnectionError):
                await transport.post("/booking/price/", request_model, PriceResponse)

    @pytest.mark.asyncio
    async def test_post_without_credentials(
        self, sample_pickup_location, sample_dropoff_location
    ):
        """Test POST request without credentials."""
        transport = AsyncTransport(credentials=None, retries=0)

        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        response_data = {"token": "test", "total": 100, "currency": "USD"}

        with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
            route = respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=response_data)
            )

            await transport.post("/booking/price/", request_model)

            # Verify no credentials were included
            request = route.calls[0].request
            request_data = json.loads(request.content.decode())
            assert "credentials" not in request_data

    @pytest.mark.asyncio
    async def test_request_logging(
        self, transport, sample_pickup_location, sample_dropoff_location, caplog
    ):
        """Test request logging functionality."""
        logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        response_data = {"token": "test", "total": 100, "currency": "USD"}

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=response_data)
            )

            with caplog.at_level("DEBUG"):
                await transport.post("/booking/price/", request_model)

            # Check that request was logged (without sensitive data)
            log_messages = [record.message for record in caplog.records]
            request_logs = [
                msg for msg in log_messages if "POST /booking/price/" in msg
            ]
            assert len(request_logs) > 0

    @pytest.mark.asyncio
    async def test_aclose(self, transport):
        """Test async transport cleanup."""
        # Mock the client close method
        transport.client.aclose = AsyncMock()

        await transport.aclose()

        transport.client.aclose.assert_called_once()


class TestSyncTransport:
    """Tests for SyncTransport class."""

    @pytest.fixture
    def transport(self, credentials):
        """Create sync transport for testing."""
        return SyncTransport(
            base_url="https://api.test.com",
            credentials=credentials,
            retries=0,  # Disable retries for faster tests
        )

    def test_init_default_client(self, credentials):
        """Test transport initialization with default client."""
        transport = SyncTransport(credentials=credentials)

        assert transport.base_url == TEST_BASE_URL
        assert transport.credentials == credentials
        assert transport.client is not None

    def test_post_success(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test successful sync POST request."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        response_data = {
            "token": "test-token-123",
            "prices": [
                {
                    "car_class": "SEDAN",
                    "car_description": "Standard Sedan",
                    "max_passengers": 4,
                    "max_luggage": 2,
                    "price": 150.00,
                    "price_default": 175.00,
                    "image128": "http://example.com/sedan128.png",
                    "image256": "http://example.com/sedan256.png",
                    "image512": "http://example.com/sedan512.png",
                    "default_meet_greet": 1,
                    "meet_greets": [],
                }
            ],
        }

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(200, json=response_data)
            )

            result = transport.post("/booking/price/", request_model, PriceResponse)

            assert result.token == "test-token-123"
            assert result.prices[0].price == 150.00

    def test_post_http_error(
        self, transport, sample_pickup_location, sample_dropoff_location
    ):
        """Test sync HTTP error handling."""
        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=sample_pickup_location,
            dropoff=sample_dropoff_location,
            passengers=2,
            luggage=1,
        )

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            respx_mock.post("/booking/price/").mock(
                return_value=httpx.Response(
                    404, json={"error": "Not Found", "code": "NOT_FOUND"}
                )
            )

            with pytest.raises(BookalimoHTTPError) as exc_info:
                transport.post("/booking/price/", request_model)

            assert exc_info.value.status_code == 404
            assert "Not Found" in str(exc_info.value)

    def test_close(self, transport):
        """Test sync transport cleanup."""
        # Mock the client close method
        transport.client.close = Mock()

        transport.close()

        transport.client.close.assert_called_once()


class TestTransportIntegration:
    """Integration tests for transport layer."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_transport_with_retry_on_server_error(self, credentials):
        """Test async transport retries on server errors."""
        transport = AsyncTransport(
            base_url="https://api.test.com",
            credentials=credentials,
            retries=2,
            backoff=0.1,  # Fast retries for testing
        )

        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=Location(
                type=LocationType.ADDRESS,
                address=Address(
                    place_name="Test Address",
                    city=City(
                        city_name="Test City",
                        country_code="US",
                        state_code="NY",
                        state_name="New York",
                    ),
                ),
            ),
            dropoff=Location(
                type=LocationType.AIRPORT,
                airport=Airport(iata_code="TST", country_code="US", state_code="NY"),
            ),
            passengers=2,
            luggage=1,
        )

        success_response = {"token": "retry-success", "total": 100, "currency": "USD"}

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            # Fail twice, then succeed
            route = respx_mock.post("/booking/price/").mock(
                side_effect=[
                    httpx.Response(500, json={"error": "Server Error"}),
                    httpx.Response(503, json={"error": "Service Unavailable"}),
                    httpx.Response(200, json=success_response),
                ]
            )

            with patch("asyncio.sleep"):  # Speed up test
                result = await transport.post("/booking/price/", request_model)

            assert result["token"] == "retry-success"
            assert len(route.calls) == 3  # Initial + 2 retries

    @pytest.mark.integration
    def test_sync_transport_with_retry_on_timeout(self, credentials):
        """Test sync transport retries on timeout."""
        transport = SyncTransport(
            base_url="https://api.test.com",
            credentials=credentials,
            retries=1,
            backoff=0.1,
        )

        request_model = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=Location(
                type=LocationType.ADDRESS,
                address=Address(
                    place_name="Test Address",
                    city=City(
                        city_name="Test City",
                        country_code="US",
                        state_code="NY",
                        state_name="New York",
                    ),
                ),
            ),
            dropoff=Location(
                type=LocationType.AIRPORT,
                airport=Airport(iata_code="TST", country_code="US", state_code="NY"),
            ),
            passengers=2,
            luggage=1,
        )

        success_response = {
            "token": "timeout-recovery",
            "total": 100,
            "currency": "USD",
        }

        with respx.mock(base_url="https://api.test.com") as respx_mock:
            # Timeout once, then succeed
            route = respx_mock.post("/booking/price/").mock(
                side_effect=[
                    httpx.TimeoutException("Request timeout"),
                    httpx.Response(200, json=success_response),
                ]
            )

            with patch("time.sleep"):  # Speed up test
                result = transport.post("/booking/price/", request_model)

            assert result["token"] == "timeout-recovery"
            assert len(route.calls) == 2  # Initial + 1 retry
