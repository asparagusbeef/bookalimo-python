"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import httpx
import pytest

from bookalimo.transport.auth import Credentials

if TYPE_CHECKING:
    from bookalimo.transport.httpx_async import AsyncTransport


@pytest.fixture
def credentials() -> Credentials:
    """Test credentials."""
    return Credentials(id="TEST_USER", password_hash="test_password", is_customer=False)


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for testing."""
    client = httpx.AsyncClient()
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
async def mock_client(
    http_client: httpx.AsyncClient, credentials: Credentials
) -> "AsyncTransport":
    """Mock client for testing."""
    from bookalimo.transport.httpx_async import AsyncTransport

    return AsyncTransport(
        client=http_client,
        credentials=credentials,
        base_url="https://sandbox.bookalimo.com",
    )
