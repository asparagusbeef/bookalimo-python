"""Pytest configuration and fixtures for comprehensive test suite."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, Optional

import httpx
import pytest
import respx
from dotenv import load_dotenv
from pydantic import BaseModel

from bookalimo import AsyncBookalimo, Bookalimo
from bookalimo.schemas.booking import (
    CreditCard,
    Location,
    LocationType,
)
from bookalimo.transport.auth import Credentials
from bookalimo.transport.httpx_async import AsyncTransport
from bookalimo.transport.httpx_sync import SyncTransport

load_dotenv()
# Test configuration
TEST_BASE_URL = "https://www.bookalimo.com/web/api"
TEST_USER_ID = "TEST_USER"
TEST_PASSWORD = "test_password"
MOCK_API_KEY = "test-google-places-key"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def credentials() -> Credentials:
    """Test credentials with proper hashing."""
    return Credentials.create(TEST_USER_ID, TEST_PASSWORD, is_customer=False)


@pytest.fixture
def customer_credentials() -> Credentials:
    """Test customer credentials."""
    return Credentials.create("CUSTOMER_ID", "customer_password", is_customer=True)


@pytest.fixture
def invalid_credentials() -> Credentials:
    """Invalid credentials for error testing."""
    return Credentials.create("INVALID_USER", "wrong_password", is_customer=False)


@pytest.fixture
def real_bookalimo_credentials() -> Optional[Credentials]:
    """Real Bookalimo testing credentials from CI environment."""
    testing_user_json = os.getenv("BOOKALIMO_TESTING_USER")
    if not testing_user_json:
        return None

    try:
        import json

        user_data = json.loads(testing_user_json)
        return Credentials.create(
            user_id=user_data["id"],
            password=user_data["password"],
            is_customer=user_data.get("is_customer", "false").lower() == "true",
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        pytest.fail(f"Invalid BOOKALIMO_TESTING_USER format: {e}")
        return None


@pytest.fixture
def skip_if_no_real_credentials(real_bookalimo_credentials):
    """Skip test if real Bookalimo credentials are not available."""
    if real_bookalimo_credentials is None:
        pytest.skip(
            "Real Bookalimo credentials not available (BOOKALIMO_TESTING_USER not set)"
        )
    return real_bookalimo_credentials


@pytest.fixture
def sample_pickup_location() -> Location:
    """Sample pickup location for testing."""
    from bookalimo.schemas.booking import Address, City

    return Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="123 Test Street",
            street_name="Test Street",
            building="123",
            zip="10001",
            city=City(
                city_name="New York",
                country_code="US",
                state_code="NY",
                state_name="New York",
            ),
        ),
    )


@pytest.fixture
def sample_dropoff_location() -> Location:
    """Sample dropoff location for testing."""
    from bookalimo.schemas.booking import Airport

    return Location(
        type=LocationType.AIRPORT,
        airport=Airport(iata_code="JFK", country_code="US", state_code="NY"),
    )


@pytest.fixture
def sample_credit_card() -> CreditCard:
    """Sample credit card for testing."""
    return CreditCard(
        number="4111111111111111",
        expiration="12/25",
        cvv="123",
        card_holder="John Doe",
        zip="10001",
    )


@pytest.fixture
def test_credit_card() -> CreditCard:
    """Test credit card for booking flow tests."""
    return CreditCard(
        number="4111111111111111",
        expiration="12/25",
        cvv="123",
        card_holder="John Doe",
        zip="10001",
    )


@pytest.fixture
def sample_price_response_data() -> Dict[str, Any]:
    """Sample price response data."""
    return {
        "token": "test-session-token-12345",
        "prices": [
            {
                "car_class": "SEDAN",
                "car_description": "Standard Sedan",
                "max_passengers": 4,
                "max_luggage": 2,
                "price": 120.00,
                "price_default": 150.00,
                "image128": "http://example.com/sedan128.png",
                "image256": "http://example.com/sedan256.png",
                "image512": "http://example.com/sedan512.png",
                "default_meet_greet": 1,
                "meet_greets": [],
            }
        ],
    }


@pytest.fixture
async def mock_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for testing."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def sync_http_client() -> Generator[httpx.Client, None, None]:
    """Sync HTTP client for testing."""
    with httpx.Client() as client:
        yield client


@pytest.fixture
async def async_transport(
    mock_http_client: httpx.AsyncClient, credentials: Credentials
) -> AsyncTransport:
    """Async transport for testing."""
    return AsyncTransport(
        client=mock_http_client,
        credentials=credentials,
        base_url=TEST_BASE_URL,
        retries=0,  # Disable retries in tests for faster execution
    )


@pytest.fixture
def sync_transport(
    sync_http_client: httpx.Client, credentials: Credentials
) -> SyncTransport:
    """Sync transport for testing."""
    return SyncTransport(
        client=sync_http_client,
        credentials=credentials,
        base_url=TEST_BASE_URL,
        retries=0,  # Disable retries in tests for faster execution
    )


@pytest.fixture
async def async_bookalimo_client(async_transport: AsyncTransport) -> AsyncBookalimo:
    """Async Bookalimo client for testing."""
    return AsyncBookalimo(transport=async_transport)


@pytest.fixture
def bookalimo_client(sync_transport: SyncTransport) -> Bookalimo:
    """Sync Bookalimo client for testing."""
    return Bookalimo(transport=sync_transport)


@pytest.fixture
def mock_respx():
    """Respx mock for HTTP requests."""
    with respx.mock(base_url=TEST_BASE_URL) as respx_mock:
        yield respx_mock


@pytest.fixture
def mock_google_places_respx():
    """Respx mock for Google Places API requests."""
    with respx.mock(base_url="https://maps.googleapis.com") as respx_mock:
        yield respx_mock


@pytest.fixture
def setup_successful_price_response(
    mock_respx: respx.MockRouter, sample_price_response_data: Dict[str, Any]
) -> None:
    """Set up successful price response mock."""
    mock_respx.post("/booking/price/").mock(
        return_value=httpx.Response(200, json=sample_price_response_data)
    )


@pytest.fixture
def setup_error_response(mock_respx: respx.MockRouter) -> None:
    """Set up error response mock."""
    mock_respx.post("/booking/price/").mock(
        return_value=httpx.Response(
            400, json={"error": "Invalid request", "code": "INVALID_REQUEST"}
        )
    )


@pytest.fixture
def setup_timeout_response(mock_respx: respx.MockRouter) -> None:
    """Set up timeout response mock."""
    mock_respx.post("/booking/price/").mock(side_effect=httpx.TimeoutException)


@pytest.fixture
def setup_network_error(mock_respx: respx.MockRouter) -> None:
    """Set up network error mock."""
    mock_respx.post("/booking/price/").mock(side_effect=httpx.ConnectError)


@pytest.fixture
def setup_server_error(mock_respx: respx.MockRouter) -> None:
    """Set up server error response mock."""
    mock_respx.post("/booking/price/").mock(
        return_value=httpx.Response(500, json={"error": "Internal Server Error"})
    )


@pytest.fixture(autouse=True)
def setup_env_vars():
    """Set up environment variables for testing."""
    original_env = os.environ.copy()

    # Set test environment variables (only if not already set)
    if "GOOGLE_PLACES_API_KEY" not in os.environ:
        os.environ["GOOGLE_PLACES_API_KEY"] = MOCK_API_KEY

    yield

    # Restore original environment (but preserve CI secrets)
    ci_secrets = {
        key: value
        for key, value in os.environ.items()
        if key in ["GOOGLE_PLACES_API_KEY", "BOOKALIMO_TESTING_USER"]
        and key in original_env
    }
    os.environ.clear()
    os.environ.update(original_env)
    os.environ.update(ci_secrets)


@pytest.fixture
def mock_places_autocomplete_response():
    """Mock Google Places autocomplete response."""
    return {
        "predictions": [
            {
                "description": "Empire State Building, 5th Avenue, New York, NY, USA",
                "place_id": "ChIJaXQRs6lZwokRY6tbFzB7VhE",
                "structured_formatting": {
                    "main_text": "Empire State Building",
                    "secondary_text": "5th Avenue, New York, NY, USA",
                },
                "types": ["establishment", "point_of_interest", "tourist_attraction"],
            }
        ],
        "status": "OK",
    }


@pytest.fixture
def mock_places_search_response():
    """Mock Google Places text search response."""
    return {
        "places": [
            {
                "id": "ChIJaXQRs6lZwokRY6tbFzB7VhE",
                "displayName": {"text": "Empire State Building"},
                "formattedAddress": "20 W 34th St, New York, NY 10001, USA",
                "location": {"latitude": 40.7484405, "longitude": -73.9856644},
                "types": ["establishment", "point_of_interest", "tourist_attraction"],
            }
        ]
    }


@contextmanager
def does_not_raise() -> Generator[None, None, None]:
    """Context manager for tests that should not raise exceptions."""
    yield


@asynccontextmanager
async def does_not_raise_async() -> AsyncGenerator[None, None]:
    """Async context manager for tests that should not raise exceptions."""
    yield


class MockResponse(BaseModel):
    """Mock response for testing."""

    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


def create_mock_response(
    status_code: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    """Create a mock HTTP response."""
    return httpx.Response(
        status_code=status_code,
        json=json_data or {},
        headers=headers or {},
    )


def create_test_address_location(
    name: str = "Test Address",
    city: str = "Test City",
    state: str = "NY",
    country: str = "US",
    zip_code: str = "10001",
    street: Optional[str] = None,
    building: Optional[str] = None,
) -> Location:
    """Helper to create test address locations with proper structure."""
    from bookalimo.schemas.booking import Address, City

    return Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name=name,
            street_name=street,
            building=building,
            zip=zip_code,
            city=City(
                city_name=city,
                country_code=country,
                state_code=state,
                state_name=state,  # Use state code as name for simplicity
            ),
        ),
    )


def create_test_airport_location(
    iata_code: str = "TST", country: str = "US", state: str = "NY"
) -> Location:
    """Helper to create test airport locations with proper structure."""
    from bookalimo.schemas.booking import Airport

    return Location(
        type=LocationType.AIRPORT,
        airport=Airport(iata_code=iata_code, country_code=country, state_code=state),
    )


@pytest.fixture
def real_pickup_location() -> Location:
    """Real pickup location for API testing."""
    from bookalimo.schemas.booking import Address, City

    return Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="Empire State Building",
            street_name="20 W 34th St",
            zip="10001",
            city=City(
                city_name="New York",
                country_code="US",
                state_code="NY",
                state_name="New York",
            ),
        ),
    )


@pytest.fixture
def real_dropoff_location() -> Location:
    """Real dropoff location for API testing."""
    from bookalimo.schemas.booking import Airport

    return Location(
        type=LocationType.AIRPORT,
        airport=Airport(iata_code="JFK", country_code="US", state_code="NY"),
    )


def assert_credentials_in_request(
    request: httpx.Request, expected_credentials: Credentials
) -> None:
    """Assert that credentials are properly included in request."""
    if hasattr(request, "content") and request.content:
        import json

        try:
            data = json.loads(request.content.decode())
            assert "credentials" in data
            creds = data["credentials"]
            assert creds["id"] == expected_credentials.id
            assert creds["password_hash"] == expected_credentials.password_hash
            assert creds["is_customer"] == expected_credentials.is_customer
        except (json.JSONDecodeError, KeyError, AttributeError):
            pytest.fail("Request should contain valid credentials")
