"""Tests for bookalimo.client."""

import httpx
import pytest
import respx

from bookalimo._client import BookALimoClient
from bookalimo.exceptions import BookALimoError
from bookalimo.models import ListReservationsResponse


@pytest.mark.asyncio
async def test_list_reservations_success(mock_client: BookALimoClient) -> None:
    """Test successful reservation listing."""
    mock_response = {"success": True, "reservations": [], "error": None}

    with respx.mock:
        respx.post("https://sandbox.bookalimo.com/booking/reservation/list/").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await mock_client.list_reservations()

        assert isinstance(result, ListReservationsResponse)
        assert result.success is True
        assert result.reservations == []


@pytest.mark.asyncio
async def test_list_reservations_api_error(mock_client: BookALimoClient) -> None:
    """Test API error handling."""
    mock_response = {"success": False, "error": "Invalid credentials"}

    with respx.mock:
        respx.post("https://sandbox.bookalimo.com/booking/reservation/list/").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        with pytest.raises(BookALimoError) as exc_info:
            await mock_client.list_reservations()

        assert "Invalid credentials" in str(exc_info.value)


@pytest.mark.asyncio
async def test_connection_error(mock_client: BookALimoClient) -> None:
    """Test connection error handling."""
    with respx.mock:
        respx.post("https://sandbox.bookalimo.com/booking/reservation/list/").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(BookALimoError) as exc_info:
            await mock_client.list_reservations()

        assert "Connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_error(mock_client: BookALimoClient) -> None:
    """Test timeout error handling."""
    with respx.mock:
        respx.post("https://sandbox.bookalimo.com/booking/reservation/list/").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        with pytest.raises(BookALimoError) as exc_info:
            await mock_client.list_reservations()

        assert "Request timeout" in str(exc_info.value)
