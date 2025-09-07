"""Main client classes for the Bookalimo SDK."""

import warnings
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .integrations.google_places import AsyncGooglePlaces, GooglePlaces

from .config import DEFAULT_BASE_URL, DEFAULT_TIMEOUTS, DEFAULT_USER_AGENT
from .exceptions import DuplicateCredentialsWarning, MissingCredentialsWarning
from .services import (
    AsyncPricingService,
    AsyncReservationsService,
    PricingService,
    ReservationsService,
)
from .transport import AsyncTransport, SyncTransport
from .transport.auth import Credentials

# Optional integrations
try:
    from .integrations.google_places import (
        AsyncGooglePlaces as _AsyncGooglePlaces,
    )
    from .integrations.google_places import (
        GooglePlaces as _GooglePlaces,
    )

    _GOOGLE_PLACES_AVAILABLE = True
except ImportError:
    _GOOGLE_PLACES_AVAILABLE = False
    _AsyncGooglePlaces = None  # type: ignore
    _GooglePlaces = None  # type: ignore


class AsyncBookalimo:
    """
    Async client for the Book-A-Limo API.

    Provides access to reservations and pricing services through a clean,
    resource-style interface. Optionally includes Google Places integration
    for location services.

    Examples:
        # Basic usage
        async with AsyncBookalimo(credentials=creds) as client:
            quote = await client.pricing.quote(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=pickup_location,
                dropoff=dropoff_location,
                passengers=2,
                luggage=2,
            )

        # With Google Places integration
        async with AsyncBookalimo(
            credentials=creds,
            google_places_api_key="your-google-api-key"
        ) as client:
            # Find locations using Google Places
            places = await client.places.search_text("Empire State Building")

            # Use in booking
            quote = await client.pricing.quote(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=pickup_location,
                dropoff=dropoff_location,
                passengers=2,
                luggage=2,
            )
    """

    def __init__(
        self,
        *,
        credentials: Optional[Credentials] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeouts: Any = DEFAULT_TIMEOUTS,
        user_agent: str = DEFAULT_USER_AGENT,
        transport: Optional[AsyncTransport] = None,
        google_places_api_key: Optional[str] = None,
    ):
        """
        Initialize the async Bookalimo client.

        Args:
            credentials: Authentication credentials (required for API calls)
            base_url: API base URL
            timeouts: Request timeout configuration
            user_agent: User agent string
            transport: Custom transport instance (optional)
            google_places_api_key: Google Places API key for location services (optional)
        """

        transport_credentials = transport.credentials if transport else None

        both_provided = all([transport_credentials, credentials])
        both_missing = not any([transport_credentials, credentials])

        if both_provided:
            warnings.warn(
                "Credentials provided in both transport and constructor. "
                "The transport credentials will be used.",
                DuplicateCredentialsWarning,
                stacklevel=2,
            )
        elif both_missing:
            warnings.warn(
                "No credentials provided in transport or constructor; proceeding unauthenticated.",
                MissingCredentialsWarning,
                stacklevel=2,
            )

        # Use whichever exists when we need to build a transport ourselves
        effective_credentials = (
            credentials if credentials is not None else transport_credentials
        )
        if transport:
            transport.credentials = effective_credentials
        self._transport = transport or AsyncTransport(
            base_url=base_url,
            timeouts=timeouts,
            user_agent=user_agent,
            credentials=effective_credentials,
        )

        # Initialize service instances
        self.reservations = AsyncReservationsService(self._transport)
        self.pricing = AsyncPricingService(self._transport)

        # Initialize Google Places integration if available
        self._google_places_api_key = google_places_api_key
        self._google_places_client: Optional[AsyncGooglePlaces] = None

    @property
    def places(self) -> "AsyncGooglePlaces":
        """
        Access Google Places integration for location services.

        Returns:
            AsyncGooglePlaces client instance

        Raises:
            ImportError: If Google Places dependencies are not installed

        Note:
            Auth priority is as follows:
              - provided api key in constructor
              - GOOGLE_PLACES_API_KEY environment variable
              - Google ADC - Except for Geocoding API.
        """
        if not _GOOGLE_PLACES_AVAILABLE:
            raise ImportError(
                "Google Places integration requires the 'places' extra. "
                "Install with: pip install bookalimo[places]"
            )

        if self._google_places_client is None:
            if _AsyncGooglePlaces is None:
                raise ImportError("Google Places integration not available")
            self._google_places_client = _AsyncGooglePlaces(
                api_key=self._google_places_api_key
            )

        return self._google_places_client

    async def aclose(self) -> None:
        """Close the client and clean up resources."""
        await self._transport.aclose()
        if self._google_places_client is not None:
            await self._google_places_client.aclose()

    async def __aenter__(self) -> "AsyncBookalimo":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.aclose()


class Bookalimo:
    """
    Sync client for the Book-A-Limo API.

    Provides access to reservations and pricing services through a clean,
    resource-style interface. Optionally includes Google Places integration
    for location services.

    Examples:
        # Basic usage
        with Bookalimo(credentials=creds) as client:
            quote = client.pricing.quote(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=pickup_location,
                dropoff=dropoff_location,
                passengers=2,
                luggage=2,
            )

        # With Google Places integration
        with Bookalimo(
            credentials=creds,
            google_places_api_key="your-google-api-key"
        ) as client:
            # Find locations using Google Places
            places = client.places.search_text("Empire State Building")

            # Use in booking
            quote = client.pricing.quote(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=pickup_location,
                dropoff=dropoff_location,
                passengers=2,
                luggage=2,
            )
    """

    def __init__(
        self,
        *,
        credentials: Optional[Credentials] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeouts: Any = DEFAULT_TIMEOUTS,
        user_agent: str = DEFAULT_USER_AGENT,
        transport: Optional[SyncTransport] = None,
        google_places_api_key: Optional[str] = None,
    ):
        """
        Initialize the sync Bookalimo client.

        Args:
            credentials: Authentication credentials (required for API calls)
            base_url: API base URL
            timeouts: Request timeout configuration
            user_agent: User agent string
            transport: Custom transport instance (optional)
            google_places_api_key: Google Places API key for location services (optional)
        """
        if transport and transport.credentials is not None and credentials is not None:
            warnings.warn(
                "Credentials provided in both transport and constructor. "
                "The transport credentials will be used.",
                UserWarning,
                stacklevel=2,
            )
        self._transport = transport or SyncTransport(
            base_url=base_url,
            timeouts=timeouts,
            user_agent=user_agent,
            credentials=credentials,
        )

        # Initialize service instances
        self.reservations = ReservationsService(self._transport)
        self.pricing = PricingService(self._transport)

        # Initialize Google Places integration if available
        self._google_places_api_key = google_places_api_key
        self._google_places_client: Optional[GooglePlaces] = None

    @property
    def places(self) -> "GooglePlaces":
        """
        Access Google Places integration for location services.

        Returns:
            GooglePlaces client instance

        Raises:
            ImportError: If Google Places dependencies are not installed

        Note:
            Auth priority is as follows:
              - provided api key in constructor
              - GOOGLE_PLACES_API_KEY environment variable
              - Google ADC - Except for Geocoding API.
        """
        if not _GOOGLE_PLACES_AVAILABLE:
            raise ImportError(
                "Google Places integration requires the 'places' extra. "
                "Install with: pip install bookalimo[places]"
            )

        if self._google_places_client is None:
            if _GooglePlaces is None:
                raise ImportError("Google Places integration not available")
            self._google_places_client = _GooglePlaces(
                api_key=self._google_places_api_key
            )

        return self._google_places_client

    def close(self) -> None:
        """Close the client and clean up resources."""
        self._transport.close()
        if self._google_places_client is not None:
            self._google_places_client.close()

    def __enter__(self) -> "Bookalimo":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
