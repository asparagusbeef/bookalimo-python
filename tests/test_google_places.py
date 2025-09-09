"""Tests for Google Places integration."""

import os
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from bookalimo.exceptions import BookalimoError

# Skip all tests if Google Places integration is not available
try:
    from google.api_core import exceptions as gexc
    from google.maps.places_v1 import PlacesClient

    from bookalimo.integrations.google_places.client_async import AsyncGooglePlaces
    from bookalimo.integrations.google_places.client_sync import GooglePlaces
    from bookalimo.integrations.google_places.common import (
        DEFAULT_PLACE_FIELDS,
        fmt_exc,
        mask_header,
    )
    from bookalimo.schemas.places import google as models
    from bookalimo.schemas.places.common import LatLng
    from bookalimo.schemas.places.place import GooglePlace as GooglePlace

    PLACES_AVAILABLE = True
except ImportError:
    PLACES_AVAILABLE = False
    # Create dummy objects for type hints when Google Places is not available
    if TYPE_CHECKING:
        from google.api_core import exceptions as gexc
        from google.maps.places_v1 import PlacesClient

        from bookalimo.integrations.google_places.client_async import AsyncGooglePlaces
        from bookalimo.integrations.google_places.client_sync import GooglePlaces
        from bookalimo.integrations.google_places.common import (
            DEFAULT_PLACE_FIELDS,
            fmt_exc,
            mask_header,
        )
        from bookalimo.schemas.places import google as models
        from bookalimo.schemas.places.common import LatLng
        from bookalimo.schemas.places.place import GooglePlace as GooglePlace
    else:
        gexc = None
        PlacesClient = None
        AsyncGooglePlaces = None
        GooglePlaces = None
        DEFAULT_PLACE_FIELDS = None
        fmt_exc = None
        mask_header = None
        models = None
        LatLng = None
        GooglePlace = None

pytestmark = pytest.mark.skipif(
    not PLACES_AVAILABLE, reason="Google Places integration not available"
)


class TestGooglePlacesCommon:
    """Tests for common utilities in Google Places integration."""

    def test_default_place_fields(self):
        """Test default place fields configuration."""
        assert isinstance(DEFAULT_PLACE_FIELDS, (list, tuple))
        assert len(DEFAULT_PLACE_FIELDS) > 0
        assert all(isinstance(field, str) for field in DEFAULT_PLACE_FIELDS)

    def test_mask_header_with_list(self):
        """Test mask header creation with list of fields."""
        fields = ["id", "displayName", "formattedAddress"]
        result = mask_header(fields)

        assert len(result) == 1
        assert result[0][0] == "x-goog-fieldmask"
        assert all(field in result[0][1] for field in fields)

    def test_mask_header_with_string(self):
        """Test mask header creation with comma-separated string."""
        fields = "id,displayName,formattedAddress"
        result = mask_header(fields)

        assert len(result) == 1
        assert result[0][0] == "x-goog-fieldmask"
        assert result[0][1] == fields

    def test_fmt_exc_with_google_exception(self):
        """Test exception formatting with Google API exception."""
        exc = gexc.InvalidArgument("Invalid field mask")
        result = fmt_exc(exc)

        assert "Invalid field mask" in result
        assert isinstance(result, str)

    def test_fmt_exc_with_regular_exception(self):
        """Test exception formatting with regular exception."""
        exc = ValueError("Regular error")
        result = fmt_exc(exc)

        assert "Regular error" in result
        assert isinstance(result, str)


@pytest.mark.skipif(
    not PLACES_AVAILABLE, reason="Google Places integration not available"
)
class TestGooglePlacesSync:
    """Tests for synchronous Google Places client."""

    @pytest.fixture
    def mock_places_client(self):
        """Mock Google Places client."""
        return Mock(spec=PlacesClient)

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for geocoding."""
        return Mock(spec=httpx.Client)

    @pytest.fixture
    def places_client(self, mock_places_client, mock_http_client):
        """Google Places client with mocked dependencies."""
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-api-key"}):
            client = GooglePlaces(
                client=mock_places_client, http_client=mock_http_client
            )
            return client

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch(
            "bookalimo.integrations.google_places.transports.PlacesClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            client = GooglePlaces(api_key="test-key-123")

            assert client.transport.client is mock_client
            mock_client_class.assert_called_once()

    def test_init_with_env_api_key(self):
        """Test initialization with environment variable API key."""
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "env-api-key"}):
            with patch(
                "bookalimo.integrations.google_places.transports.PlacesClient"
            ) as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client

                client = GooglePlaces()

                assert client.transport.client is mock_client
                mock_client_class.assert_called_once()

    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google Places API key is required"):
                GooglePlaces()

    def test_init_with_custom_client(self, mock_places_client):
        """Test initialization with custom client."""
        client = GooglePlaces(client=mock_places_client)
        assert client.transport.client is mock_places_client

    def test_context_manager(self, places_client):
        """Test context manager functionality."""
        with places_client as client:
            assert isinstance(client, GooglePlaces)

        # Should have called close
        places_client.transport.client.transport.close.assert_called_once()

    def test_close(self, places_client):
        """Test close functionality."""
        places_client.transport.client.transport.close = Mock()
        places_client.http_client.close = Mock()

        places_client.close()

        places_client.transport.client.transport.close.assert_called_once()
        places_client.http_client.close.assert_called_once()

    def test_autocomplete_success(self, places_client):
        """Test successful autocomplete request."""
        # Mock request
        request = models.AutocompletePlacesRequest(
            input="Empire State Building", location_bias=None
        )

        # Mock proto response from transport
        mock_proto_response = Mock()

        expected_response = models.AutocompletePlacesResponse(
            suggestions=[
                models.Suggestion(
                    place_prediction=models.PlacePrediction(
                        place_id="test-place-id",
                        place="places/test-place-id",
                        text=models.FormattableText(text="Empire State Building"),
                    )
                )
            ]
        )

        with (
            patch.object(
                places_client.transport, "autocomplete_places"
            ) as mock_transport,
            patch(
                "bookalimo.integrations.google_places.client_sync.validate_proto_to_model"
            ) as mock_validate,
        ):
            mock_transport.return_value = mock_proto_response
            mock_validate.return_value = expected_response

            result = places_client.autocomplete(request=request)

            assert result == expected_response
            mock_transport.assert_called_once_with(request=request.model_dump())
            mock_validate.assert_called_once_with(
                mock_proto_response, models.AutocompletePlacesResponse
            )

    def test_autocomplete_google_api_error(self, places_client):
        """Test autocomplete with Google API error."""
        request = models.AutocompletePlacesRequest(
            input="Test Query", location_bias=None
        )

        places_client.transport.client.autocomplete_places.side_effect = (
            gexc.InvalidArgument("Invalid request")
        )

        with pytest.raises(BookalimoError, match="Google Places Autocomplete failed"):
            places_client.autocomplete(request=request)

    def test_search_success(self, places_client):
        """Test successful text search."""
        mock_proto_response = Mock()
        mock_proto_response.places = [Mock(), Mock()]  # Two places
        places_client.transport.client.search_text.return_value = mock_proto_response

        with patch(
            "bookalimo.integrations.google_places.proto_adapter.validate_proto_to_model"
        ) as mock_validate:
            mock_google_place = GooglePlace(
                formatted_address="Test Place",
                location=LatLng(latitude=0.0, longitude=0.0),
            )
            # Mock should return GooglePlace object, not list containing models.Place
            mock_validate.return_value = mock_google_place

            result = places_client.search("Empire State Building")

            assert len(result) == 2
            assert all(isinstance(place, models.Place) for place in result)
            assert all(place.formatted_address == "Test Place" for place in result)
            assert all(place.google_place == mock_google_place for place in result)
            places_client.transport.client.search_text.assert_called_once()

            # Verify metadata (field mask) was set
            call_kwargs = places_client.transport.client.search_text.call_args[1]
            assert "metadata" in call_kwargs

    def test_search_with_custom_fields(self, places_client):
        """Test text search with custom field selection."""
        mock_proto_response = Mock()
        mock_proto_response.places = []
        places_client.transport.client.search_text.return_value = mock_proto_response

        custom_fields = ["id", "displayName", "formattedAddress"]
        places_client.search("Test Query", fields=custom_fields)

        call_kwargs = places_client.transport.client.search_text.call_args[1]
        assert "metadata" in call_kwargs
        metadata = call_kwargs["metadata"]
        assert len(metadata) == 1
        assert metadata[0][0] == "x-goog-fieldmask"

    def test_search_invalid_argument_error(self, places_client):
        """Test search with invalid argument error."""
        places_client.transport.client.search_text.side_effect = gexc.InvalidArgument(
            "Invalid field mask"
        )

        with pytest.raises(
            BookalimoError, match="Google Places Text Search invalid argument"
        ):
            places_client.search("Test Query")

    def test_search_general_google_api_error(self, places_client):
        """Test search with general Google API error."""
        places_client.transport.client.search_text.side_effect = gexc.PermissionDenied(
            "API key invalid"
        )

        with pytest.raises(BookalimoError, match="Google Places Text Search failed"):
            places_client.search("Test Query")

    def test_get_place_success(self, places_client):
        """Test successful get place request."""
        place_id = "test-place-id"
        mock_proto_response = Mock()
        places_client.transport.client.get_place.return_value = mock_proto_response

        with patch(
            "bookalimo.integrations.google_places.proto_adapter.validate_proto_to_model"
        ) as mock_validate:
            mock_google_place = GooglePlace(
                formatted_address="Test Place",
                location=LatLng(latitude=40.7128, longitude=-74.0060),
            )
            # Mock should return GooglePlace object, not list containing models.Place
            mock_validate.return_value = mock_google_place

            result = places_client.get(place_id)

            assert isinstance(result, models.Place)
            assert result.formatted_address == "Test Place"
            assert result.lat == 40.7128
            assert result.lng == -74.0060
            assert result.google_place == mock_google_place
            places_client.transport.client.get_place.assert_called_once()

            # Verify the request format
            call_args = places_client.transport.client.get_place.call_args[1]
            assert call_args["request"]["name"] == f"places/{place_id}"

    def test_get_place_not_found(self, places_client):
        """Test get place when place is not found."""
        places_client.transport.client.get_place.side_effect = gexc.NotFound(
            "Place not found"
        )

        result = places_client.get("nonexistent-place-id")

        assert result is None

    def test_get_place_invalid_argument_error(self, places_client):
        """Test get place with invalid argument error."""
        places_client.transport.client.get_place.side_effect = gexc.InvalidArgument(
            "Invalid place ID"
        )

        with pytest.raises(
            BookalimoError, match="Google Places Get Place invalid argument"
        ):
            places_client.get("invalid-place-id")

    def test_geocode_success(self, places_client):
        """Test successful geocoding request."""
        request = models.GeocodingRequest(address="123 Main St, New York, NY")

        expected_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "123 Main St, New York, NY 10001, USA",
                    "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}},
                }
            ],
        }

        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        places_client.http_client.get.return_value = mock_response

        result = places_client.geocode(request)

        assert result == expected_response
        places_client.http_client.get.assert_called_once()

        # Verify URL and parameters
        call_args = places_client.http_client.get.call_args
        assert "https://maps.googleapis.com/maps/api/geocode/json" in call_args[0]
        assert "params" in call_args[1]

    def test_geocode_http_error(self, places_client):
        """Test geocoding with HTTP error."""
        request = models.GeocodingRequest(address="Test Address")

        places_client.http_client.get.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=Mock()
        )

        with pytest.raises(BookalimoError, match="HTTP geocoding failed"):
            places_client.geocode(request)


@pytest.mark.skipif(
    not PLACES_AVAILABLE, reason="Google Places integration not available"
)
class TestGooglePlacesAsync:
    """Tests for asynchronous Google Places client."""

    @pytest.fixture
    def mock_places_client(self):
        """Mock async Google Places client."""
        return Mock()

    @pytest.fixture
    def mock_http_client(self):
        """Mock async HTTP client for geocoding."""
        return Mock(spec=httpx.AsyncClient)

    @pytest.fixture
    def places_client(self, mock_places_client, mock_http_client):
        """Async Google Places client with mocked dependencies."""
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-api-key"}):
            client = AsyncGooglePlaces(
                client=mock_places_client, http_client=mock_http_client
            )
            return client

    @pytest.mark.asyncio
    async def test_init_with_api_key(self):
        """Test async initialization with API key."""
        with patch(
            "bookalimo.integrations.google_places.transports.PlacesAsyncClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            client = AsyncGooglePlaces(api_key="async-test-key-123")

            assert client.transport.client is mock_client
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_without_api_key_raises_error(self):
        """Test async initialization without API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google Places API key is required"):
                AsyncGooglePlaces()

    @pytest.mark.asyncio
    async def test_context_manager(self, places_client):
        """Test async context manager functionality."""
        places_client.aclose = AsyncMock()

        async with places_client as client:
            assert isinstance(client, AsyncGooglePlaces)

        places_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_aclose(self, places_client):
        """Test async close functionality."""
        places_client.transport.client.transport.close = AsyncMock()
        places_client.http_client.aclose = AsyncMock()

        await places_client.aclose()

        places_client.transport.client.transport.close.assert_called_once()
        places_client.http_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_autocomplete_success(self, places_client):
        """Test successful async autocomplete request."""
        request = models.AutocompletePlacesRequest(
            input="Empire State Building", location_bias=None
        )

        # Mock proto response from transport
        mock_proto_response = Mock()

        expected_response = models.AutocompletePlacesResponse(
            suggestions=[
                models.Suggestion(
                    place_prediction=models.PlacePrediction(
                        place="places/async-place-id",
                        place_id="async-place-id",
                        text=models.FormattableText(text="Empire State Building"),
                    )
                )
            ]
        )

        with (
            patch.object(
                places_client.transport, "autocomplete_places", new_callable=AsyncMock
            ) as mock_transport,
            patch(
                "bookalimo.integrations.google_places.client_async.validate_proto_to_model"
            ) as mock_validate,
        ):
            mock_transport.return_value = mock_proto_response
            mock_validate.return_value = expected_response

            result = await places_client.autocomplete(request=request)

            assert result == expected_response
            mock_transport.assert_called_once_with(request=request.model_dump())
            mock_validate.assert_called_once_with(
                mock_proto_response, models.AutocompletePlacesResponse
            )

    @pytest.mark.asyncio
    async def test_search_success(self, places_client):
        """Test successful async text search."""
        mock_proto_response = Mock()
        mock_proto_response.places = [Mock()]
        places_client.transport.client.search_text = AsyncMock(
            return_value=mock_proto_response
        )

        with patch(
            "bookalimo.integrations.google_places.proto_adapter.validate_proto_to_model"
        ) as mock_validate:
            mock_google_place = GooglePlace(
                formatted_address="Async Test Place",
                location=LatLng(latitude=40.7128, longitude=-74.0060),
            )
            # Mock should return GooglePlace object, not list containing models.Place
            mock_validate.return_value = mock_google_place

            result = await places_client.search("Async Test Query")

            assert len(result) == 1
            assert isinstance(result[0], models.Place)
            assert result[0].formatted_address == "Async Test Place"
            assert result[0].lat == 40.7128
            assert result[0].lng == -74.0060
            places_client.transport.client.search_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_place_success(self, places_client):
        """Test successful async get place request."""
        place_id = "async-test-place-id"
        mock_proto_response = Mock()
        places_client.transport.client.get_place = AsyncMock(
            return_value=mock_proto_response
        )

        with patch(
            "bookalimo.integrations.google_places.proto_adapter.validate_proto_to_model"
        ) as mock_validate:
            mock_google_place = GooglePlace(
                formatted_address="Async Test Place",
                location=LatLng(latitude=40.7128, longitude=-74.0060),
            )
            # Mock should return GooglePlace object, not list containing models.Place
            mock_validate.return_value = mock_google_place

            result = await places_client.get(place_id)

            assert isinstance(result, models.Place)
            assert result.formatted_address == "Async Test Place"
            assert result.lat == 40.7128
            assert result.lng == -74.0060
            assert result.google_place == mock_google_place
            places_client.transport.client.get_place.assert_called_once()

    @pytest.mark.asyncio
    async def test_geocode_success(self, places_client):
        """Test successful async geocoding request."""
        request = models.GeocodingRequest(address="123 Async St, New York, NY")

        expected_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "123 Async St, New York, NY 10001, USA",
                    "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}},
                }
            ],
        }

        # Mock async HTTP response
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        places_client.http_client.get = AsyncMock(return_value=mock_response)

        result = await places_client.geocode(request)

        assert result == expected_response
        places_client.http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_geocode_http_error(self, places_client):
        """Test async geocoding with HTTP error."""
        request = models.GeocodingRequest(address="Async Test Address")

        places_client.http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Bad Request", request=Mock(), response=Mock()
            )
        )

        with pytest.raises(BookalimoError, match="HTTP geocoding failed"):
            await places_client.geocode(request)


class TestGooglePlacesIntegration:
    """Integration tests for Google Places (when available)."""

    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.skipif(
        not PLACES_AVAILABLE, reason="Google Places integration not available"
    )
    def test_real_api_search(self):
        """Test real API search (requires valid API key)."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key or api_key == "test-google-places-key":
            pytest.skip("Real Google Places API key required for integration test")

        client = GooglePlaces(api_key=api_key)

        try:
            # Search for a well-known location
            results = client.search("Empire State Building New York", fields=["*"])

            assert isinstance(results, list)
            if results:  # API returned results
                assert all(isinstance(place, models.Place) for place in results)
                # Check that at least one result contains relevant information
                formatted_addresses = [
                    place.formatted_address.lower()
                    for place in results
                    if place.formatted_address
                ]
                assert any(
                    "20 w 34th st" in formatted_address
                    for formatted_address in formatted_addresses
                ), (
                    f"No result contains relevant information - empire not in {formatted_addresses}"
                )
        except BookalimoError as e:
            if "400" in str(e) or "invalid argument" in str(e).lower():
                raise e
            pytest.skip(f"Google Places API call failed: {e}")
        finally:
            client.close()

    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.skipif(
        not PLACES_AVAILABLE, reason="Google Places integration not available"
    )
    @pytest.mark.asyncio
    async def test_real_api_search_async(self):
        """Test real async API search (requires valid API key)."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key or api_key == "test-google-places-key":
            pytest.skip("Real Google Places API key required for integration test")

        async with AsyncGooglePlaces(api_key=api_key) as client:
            try:
                # Search for a well-known location
                results = await client.search("The white house")

                assert isinstance(results, list)
                if results:  # API returned results
                    assert all(isinstance(place, models.Place) for place in results)
                    # Check that at least one result contains relevant information
                    formatted_addresses = [
                        place.formatted_address.lower()
                        for place in results
                        if place.formatted_address
                    ]
                    assert any(
                        "1600 pennsylvania ave" in formatted_address
                        for formatted_address in formatted_addresses
                    ), (
                        f"No result contains relevant information - white house not in {formatted_addresses}"
                    )
            except BookalimoError as e:
                if "400" in str(e) or "invalid argument" in str(e).lower():
                    raise e
                pytest.skip(f"Google Places API call failed: {e}")

    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.skipif(
        not PLACES_AVAILABLE, reason="Google Places integration not available"
    )
    def test_real_geocoding_api(self):
        """Test real geocoding API (requires valid API key)."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key or api_key == "test-google-places-key":
            pytest.skip("Real Google Places API key required for integration test")

        with GooglePlaces(api_key=api_key) as client:
            try:
                request = models.GeocodingRequest(
                    address="1600 Amphitheatre Parkway, Mountain View, CA"
                )

                result = client.geocode(request)

                assert isinstance(result, dict)
                assert "status" in result
                if result["status"] == "OK":
                    assert "results" in result
                    assert len(result["results"]) > 0
                    first_result = result["results"][0]
                    assert "geometry" in first_result
                    assert "location" in first_result["geometry"]
            except BookalimoError as e:
                if "400" in str(e) or "invalid argument" in str(e).lower():
                    raise e
                pytest.skip(f"Geocoding API call failed: {e}")


class TestGooglePlacesErrorHandling:
    """Tests for error handling in Google Places integration."""

    @pytest.mark.skipif(
        not PLACES_AVAILABLE, reason="Google Places integration not available"
    )
    def test_handles_quota_exceeded_error(self):
        """Test handling of quota exceeded errors."""
        mock_client = Mock()
        mock_client.search_text.side_effect = gexc.ResourceExhausted("Quota exceeded")

        places_client = GooglePlaces(client=mock_client)

        with pytest.raises(BookalimoError, match="Google Places Text Search failed"):
            places_client.search("Test Query")

    @pytest.mark.skipif(
        not PLACES_AVAILABLE, reason="Google Places integration not available"
    )
    def test_handles_permission_denied_error(self):
        """Test handling of permission denied errors."""
        mock_client = Mock()
        mock_client.autocomplete_places.side_effect = gexc.PermissionDenied(
            "API key invalid"
        )

        places_client = GooglePlaces(client=mock_client)

        request = models.AutocompletePlacesRequest(
            input="Test Query", location_bias=None
        )

        with pytest.raises(BookalimoError, match="Google Places Autocomplete failed"):
            places_client.autocomplete(request=request)

    @pytest.mark.skipif(
        not PLACES_AVAILABLE, reason="Google Places integration not available"
    )
    def test_handles_network_timeout(self):
        """Test handling of network timeouts in HTTP requests."""
        mock_http_client = Mock()
        mock_http_client.get.side_effect = httpx.TimeoutException("Request timeout")

        places_client = GooglePlaces(api_key="test-key", http_client=mock_http_client)

        request = models.GeocodingRequest(address="Test Address")

        with pytest.raises(BookalimoError, match="HTTP geocoding failed"):
            places_client.geocode(request)
