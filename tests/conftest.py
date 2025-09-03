"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import httpx
import pytest

from bookalimo import create_credentials
from bookalimo.models import Credentials

if TYPE_CHECKING:
    from bookalimo._client import BookALimoClient


@pytest.fixture
def credentials() -> Credentials:
    """Test credentials."""
    return create_credentials("TEST_USER", "test_password")


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
) -> "BookALimoClient":
    """Mock client for testing."""
    from bookalimo._client import BookALimoClient

    return BookALimoClient(http_client, credentials)
