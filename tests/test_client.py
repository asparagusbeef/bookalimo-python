"""Tests for the main Bookalimo client classes."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bookalimo import AsyncBookalimo, Bookalimo
from bookalimo.exceptions import (
    DuplicateCredentialsWarning,
    MissingCredentialsWarning,
)
from bookalimo.services import (
    AsyncPricingService,
    AsyncReservationsService,
    PricingService,
    ReservationsService,
)
from bookalimo.transport.auth import Credentials
from bookalimo.transport.httpx_async import AsyncTransport
from bookalimo.transport.httpx_sync import SyncTransport


class TestAsyncBookalimo:
    """Tests for AsyncBookalimo client."""

    def test_init_with_credentials(self, credentials):
        """Test client initialization with credentials."""
        client = AsyncBookalimo(credentials=credentials)

        assert client._transport is not None
        assert isinstance(client._transport, AsyncTransport)
        assert client._transport.credentials == credentials
        assert isinstance(client.reservations, AsyncReservationsService)
        assert isinstance(client.pricing, AsyncPricingService)
        assert client._google_places_client is None

    def test_init_with_transport(self, async_transport):
        """Test client initialization with custom transport."""
        client = AsyncBookalimo(transport=async_transport)

        assert client._transport is async_transport
        assert isinstance(client.reservations, AsyncReservationsService)
        assert isinstance(client.pricing, AsyncPricingService)

    def test_init_with_both_credentials_and_transport(
        self, credentials, async_transport
    ):
        """Test initialization with both credentials and transport warns appropriately."""
        with pytest.warns(DuplicateCredentialsWarning):
            client = AsyncBookalimo(credentials=credentials, transport=async_transport)

        # Transport credentials should take precedence
        assert client._transport is async_transport

    def test_init_without_credentials_warns(self):
        """Test initialization without credentials issues warning."""
        with pytest.warns(MissingCredentialsWarning):
            client = AsyncBookalimo()

        assert client._transport is not None
        assert client._transport.credentials is None

    def test_init_with_google_places_api_key(self, credentials):
        """Test initialization with Google Places API key."""
        client = AsyncBookalimo(
            credentials=credentials, google_places_api_key="test-key"
        )

        assert client._google_places_api_key == "test-key"
        assert client._google_places_client is None  # Lazy initialization

    def test_init_custom_config(self, credentials):
        """Test initialization with custom configuration."""
        custom_base_url = "https://custom.api.com"
        custom_user_agent = "TestAgent/1.0"

        client = AsyncBookalimo(
            credentials=credentials,
            base_url=custom_base_url,
            user_agent=custom_user_agent,
        )

        assert client._transport.base_url == custom_base_url
        assert client._transport.headers["user-agent"] == custom_user_agent

    @pytest.mark.asyncio
    async def test_context_manager(self, credentials):
        """Test async context manager functionality."""
        async with AsyncBookalimo(credentials=credentials) as client:
            assert isinstance(client, AsyncBookalimo)
            assert client._transport is not None

    @pytest.mark.asyncio
    async def test_close_cleanup(self, credentials):
        """Test proper cleanup on close."""
        client = AsyncBookalimo(credentials=credentials)

        # Mock the transport close method
        with patch.object(client._transport, "aclose", new=AsyncMock()) as mock_aclose:
            await client.aclose()
            mock_aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_cleanup_with_places_client(self, credentials):
        """Test cleanup with Google Places client."""
        with (
            patch("bookalimo.client._GOOGLE_PLACES_AVAILABLE", True),
            patch("bookalimo.client._AsyncGooglePlaces") as mock_places_class,
        ):
            mock_places_instance = Mock()
            mock_places_instance.aclose = AsyncMock(return_value=None)
            mock_places_class.return_value = mock_places_instance

            client = AsyncBookalimo(
                credentials=credentials, google_places_api_key="test-key"
            )

            # Access places to trigger lazy initialization
            try:
                _ = client.places
                client._google_places_client = mock_places_instance
            except ImportError:
                # Skip if places integration not available
                return

            with patch.object(
                client._transport, "aclose", new=AsyncMock()
            ) as mock_aclose:
                await client.aclose()
                mock_aclose.assert_called_once()
            if client._google_places_client:
                mock_places_instance.aclose.assert_called_once()

    def test_places_property_without_integration(self, credentials):
        """Test places property raises ImportError when integration unavailable."""
        with patch("bookalimo.client._GOOGLE_PLACES_AVAILABLE", False):
            client = AsyncBookalimo(credentials=credentials)

            with pytest.raises(ImportError, match="Google Places integration requires"):
                _ = client.places

    def test_places_property_lazy_initialization(self, credentials):
        """Test places property lazy initialization."""
        with (
            patch("bookalimo.client._GOOGLE_PLACES_AVAILABLE", True),
            patch("bookalimo.client._AsyncGooglePlaces") as mock_places_class,
        ):
            mock_places_instance = Mock()
            mock_places_class.return_value = mock_places_instance

            client = AsyncBookalimo(
                credentials=credentials, google_places_api_key="test-key"
            )

            # First access should create instance
            try:
                places1 = client.places
                assert places1 is mock_places_instance
                mock_places_class.assert_called_once_with(api_key="test-key")

                # Second access should return same instance
                places2 = client.places
                assert places2 is places1
                assert mock_places_class.call_count == 1  # Not called again
            except ImportError:
                # Skip if places integration not available in test environment
                pytest.skip("Google Places integration not available")


class TestBookalimo:
    """Tests for sync Bookalimo client."""

    def test_init_with_credentials(self, credentials):
        """Test client initialization with credentials."""
        client = Bookalimo(credentials=credentials)

        assert client._transport is not None
        assert isinstance(client._transport, SyncTransport)
        assert client._transport.credentials == credentials
        assert isinstance(client.reservations, ReservationsService)
        assert isinstance(client.pricing, PricingService)
        assert client._google_places_client is None

    def test_init_with_transport(self, sync_transport):
        """Test client initialization with custom transport."""
        client = Bookalimo(transport=sync_transport)

        assert client._transport is sync_transport
        assert isinstance(client.reservations, ReservationsService)
        assert isinstance(client.pricing, PricingService)

    def test_init_with_both_credentials_and_transport_warns(
        self, credentials, sync_transport
    ):
        """Test initialization with both credentials and transport warns."""
        with pytest.warns(UserWarning):
            client = Bookalimo(credentials=credentials, transport=sync_transport)

        # Transport should be used as-is
        assert client._transport is sync_transport

    def test_init_with_google_places_api_key(self, credentials):
        """Test initialization with Google Places API key."""
        client = Bookalimo(credentials=credentials, google_places_api_key="test-key")

        assert client._google_places_api_key == "test-key"
        assert client._google_places_client is None  # Lazy initialization

    def test_init_custom_config(self, credentials):
        """Test initialization with custom configuration."""
        custom_base_url = "https://custom.api.com"
        custom_user_agent = "TestAgent/1.0"

        client = Bookalimo(
            credentials=credentials,
            base_url=custom_base_url,
            user_agent=custom_user_agent,
        )

        assert client._transport.base_url == custom_base_url
        assert client._transport.headers["user-agent"] == custom_user_agent

    def test_context_manager(self, credentials):
        """Test sync context manager functionality."""
        with Bookalimo(credentials=credentials) as client:
            assert isinstance(client, Bookalimo)
            assert client._transport is not None

    def test_close_cleanup(self, credentials):
        """Test proper cleanup on close."""
        client = Bookalimo(credentials=credentials)

        # Mock the transport close method
        with patch.object(client._transport, "close", new=Mock()) as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_close_cleanup_with_places_client(self, credentials):
        """Test cleanup with Google Places client."""
        with (
            patch("bookalimo.client._GOOGLE_PLACES_AVAILABLE", True),
            patch("bookalimo.client._GooglePlaces") as mock_places_class,
        ):
            mock_places_instance = Mock()
            mock_places_instance.close = Mock()
            mock_places_class.return_value = mock_places_instance

            client = Bookalimo(
                credentials=credentials, google_places_api_key="test-key"
            )

            # Access places to trigger lazy initialization
            try:
                _ = client.places
                client._google_places_client = mock_places_instance
            except ImportError:
                # Skip if places integration not available
                return

            with patch.object(client._transport, "close", new=Mock()) as mock_close:
                client.close()
                mock_close.assert_called_once()
            if client._google_places_client:
                mock_places_instance.close.assert_called_once()

    def test_places_property_without_integration(self, credentials):
        """Test places property raises ImportError when integration unavailable."""
        with patch("bookalimo.client._GOOGLE_PLACES_AVAILABLE", False):
            client = Bookalimo(credentials=credentials)

            with pytest.raises(ImportError, match="Google Places integration requires"):
                _ = client.places

    def test_places_property_lazy_initialization(self, credentials):
        """Test places property lazy initialization."""
        with (
            patch("bookalimo.client._GOOGLE_PLACES_AVAILABLE", True),
            patch("bookalimo.client._GooglePlaces") as mock_places_class,
        ):
            mock_places_instance = Mock()
            mock_places_class.return_value = mock_places_instance

            client = Bookalimo(
                credentials=credentials, google_places_api_key="test-key"
            )

            # First access should create instance
            try:
                places1 = client.places
                assert places1 is mock_places_instance
                mock_places_class.assert_called_once_with(api_key="test-key")

                # Second access should return same instance
                places2 = client.places
                assert places2 is places1
                assert mock_places_class.call_count == 1  # Not called again
            except ImportError:
                # Skip if places integration not available in test environment
                pytest.skip("Google Places integration not available")


class TestClientCreationEdgeCases:
    """Test edge cases in client creation."""

    def test_credentials_precedence_with_different_values(self):
        """Test credential precedence when different values provided."""
        creds1 = Credentials.create("user1", "pass1")
        creds2 = Credentials.create("user2", "pass2")

        # Create transport with credentials
        transport = AsyncTransport(credentials=creds1)

        # Create client with different credentials
        with pytest.warns(DuplicateCredentialsWarning):
            client = AsyncBookalimo(credentials=creds2, transport=transport)

        # Transport credentials should be used but updated
        assert client._transport.credentials == creds2

    def test_none_credentials_handling(self):
        """Test handling of None credentials in various scenarios."""
        transport = AsyncTransport(credentials=None)

        with pytest.warns(MissingCredentialsWarning):
            client = AsyncBookalimo(transport=transport, credentials=None)

        assert client._transport.credentials is None
