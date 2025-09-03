"""Tests for bookalimo.wrapper."""

import httpx
import pytest
import respx

from bookalimo import (
    BookALimo,
    create_address_location,
    create_airport_location,
    create_credentials,
)
from bookalimo.models import RateType


@pytest.mark.asyncio
async def test_wrapper_context_manager() -> None:
    """Test wrapper as async context manager."""
    credentials = create_credentials("TEST", "password")

    async with httpx.AsyncClient() as http_client:
        async with BookALimo(credentials, http_client=http_client) as wrapper:
            assert wrapper is not None
            assert hasattr(wrapper, "client")


@pytest.mark.asyncio
async def test_get_prices() -> None:
    """Test price retrieval."""
    credentials = create_credentials("TEST", "password")
    pickup = create_airport_location("JFK", "New York")
    dropoff = create_address_location("123 Main St")

    mock_response = {
        "token": "ABC123",
        "prices": [
            {
                "carClass": "SD",
                "carDescription": "Sedan",
                "maxPassengers": 3,
                "maxLuggage": 3,
                "price": 100.0,
                "priceDefault": 110.0,
                "image128": "url",
                "image256": "url",
                "image512": "url",
                "defaultMeetGreet": None,
                "meetGreets": [],
            }
        ],
    }

    async with httpx.AsyncClient() as http_client:
        async with BookALimo(credentials, http_client=http_client) as wrapper:
            with respx.mock:
                respx.post().mock(return_value=httpx.Response(200, json=mock_response))

                result = await wrapper.get_prices(
                    rate_type=RateType.P2P,
                    date_time="09/05/2025 12:44 AM",
                    pickup=pickup,
                    dropoff=dropoff,
                    passengers=2,
                    luggage=3,
                )

                assert result.token == "ABC123"
                assert len(result.prices) == 1
                assert result.prices[0].car_class == "SD"
