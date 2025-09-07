"""Tests for Google Places integration."""

import os
from unittest.mock import Mock, patch, AsyncMock

import pytest
import httpx
import respx
from google.api_core import exceptions as gexc

from bookalimo.exceptions import BookalimoError
from bookalimo.integrations.google_places.client_async import AsyncGooglePlaces
from bookalimo.integrations.google_places.client_sync import GooglePlaces
from bookalimo.integrations.google_places.common import DEFAULT_PLACE_FIELDS, fmt_exc, mask_header
from bookalimo.schemas.places import google as models


# Skip all tests if Google Places integration is not available
try:
    from google.maps.places_v1 import PlacesClient
    PLACES_AVAILABLE = True
except ImportError:
    PLACES_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")


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

    def test_fmt_exc_with_none(self):
        """Test exception formatting with None."""
        result = fmt_exc(None)
        assert result == "Unknown error"


@pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
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
            client = GooglePlaces(client=mock_places_client, http_client=mock_http_client)
            return client

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch("bookalimo.integrations.google_places.client_sync.PlacesClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = GooglePlaces(api_key="test-key-123")
            
            assert client.client is mock_client
            mock_client_class.assert_called_once()

    def test_init_with_env_api_key(self):
        """Test initialization with environment variable API key."""
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "env-api-key"}):
            with patch("bookalimo.integrations.google_places.client_sync.PlacesClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                client = GooglePlaces()
                
                assert client.client is mock_client
                mock_client_class.assert_called_once()

    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google Places API key is required"):
                GooglePlaces()

    def test_init_with_custom_client(self, mock_places_client):
        """Test initialization with custom client."""
        client = GooglePlaces(client=mock_places_client)
        assert client.client is mock_places_client

    def test_context_manager(self, places_client):
        """Test context manager functionality."""
        with places_client as client:
            assert isinstance(client, GooglePlaces)
        
        # Should have called close
        places_client.client.transport.close.assert_called_once()

    def test_close(self, places_client):
        """Test close functionality."""
        places_client.client.transport.close = Mock()
        places_client.http_client.close = Mock()
        
        places_client.close()
        
        places_client.client.transport.close.assert_called_once()
        places_client.http_client.close.assert_called_once()

    def test_autocomplete_success(self, places_client):
        """Test successful autocomplete request."""
        # Mock request
        request = models.AutocompletePlacesRequest(
            input="Empire State Building",
            location_bias=None
        )
        
        # Mock response from Google Places API
        mock_proto_response = Mock()
        places_client.client.autocomplete_places.return_value = mock_proto_response
        
        # Mock validation function
        with patch("bookalimo.integrations.google_places.client_sync.validate_proto_to_model") as mock_validate:
            expected_response = models.AutocompletePlacesResponse(
                suggestions=[
                    models.AutocompletePlacesSuggestion(
                        place_id="test-place-id",
                        text="Empire State Building"
                    )
                ]
            )
            mock_validate.return_value = expected_response
            
            result = places_client.autocomplete(request)
            
            assert result == expected_response
            places_client.client.autocomplete_places.assert_called_once()
            mock_validate.assert_called_once_with(mock_proto_response, models.AutocompletePlacesResponse)

    def test_autocomplete_google_api_error(self, places_client):
        """Test autocomplete with Google API error."""
        request = models.AutocompletePlacesRequest(
            input="Test Query",
            location_bias=None
        )
        
        places_client.client.autocomplete_places.side_effect = gexc.InvalidArgument("Invalid request")
        
        with pytest.raises(BookalimoError, match="Google Places Autocomplete failed"):
            places_client.autocomplete(request)

    def test_search_success(self, places_client):
        """Test successful text search."""
        mock_proto_response = Mock()
        mock_proto_response.places = [Mock(), Mock()]  # Two places
        places_client.client.search_text.return_value = mock_proto_response
        
        with patch("bookalimo.integrations.google_places.client_sync.validate_proto_to_model") as mock_validate:
            mock_place = models.Place(
                id="test-place-id",
                display_name="Test Place"
            )
            mock_validate.return_value = mock_place
            
            result = places_client.search("Empire State Building")
            
            assert len(result) == 2
            assert all(place == mock_place for place in result)
            places_client.client.search_text.assert_called_once()
            
            # Verify metadata (field mask) was set
            call_kwargs = places_client.client.search_text.call_args[1]
            assert "metadata" in call_kwargs

    def test_search_with_custom_fields(self, places_client):
        """Test text search with custom field selection."""
        mock_proto_response = Mock()
        mock_proto_response.places = []
        places_client.client.search_text.return_value = mock_proto_response
        
        custom_fields = ["id", "displayName", "formattedAddress"]
        places_client.search("Test Query", fields=custom_fields)
        
        call_kwargs = places_client.client.search_text.call_args[1]
        assert "metadata" in call_kwargs
        metadata = call_kwargs["metadata"]
        assert len(metadata) == 1
        assert metadata[0][0] == "x-goog-fieldmask"

    def test_search_invalid_argument_error(self, places_client):
        """Test search with invalid argument error."""
        places_client.client.search_text.side_effect = gexc.InvalidArgument("Invalid field mask")
        
        with pytest.raises(BookalimoError, match="Google Places Text Search invalid argument"):
            places_client.search("Test Query")

    def test_search_general_google_api_error(self, places_client):
        """Test search with general Google API error."""
        places_client.client.search_text.side_effect = gexc.PermissionDenied("API key invalid")
        
        with pytest.raises(BookalimoError, match="Google Places Text Search failed"):
            places_client.search("Test Query")

    def test_get_place_success(self, places_client):
        """Test successful get place request."""
        place_id = "test-place-id"
        mock_proto_response = Mock()
        places_client.client.get_place.return_value = mock_proto_response
        
        with patch("bookalimo.integrations.google_places.client_sync.validate_proto_to_model") as mock_validate:
            expected_place = models.Place(
                id=place_id,
                display_name="Test Place"
            )
            mock_validate.return_value = expected_place
            
            result = places_client.get(place_id)
            
            assert result == expected_place
            places_client.client.get_place.assert_called_once()
            
            # Verify the request format
            call_args = places_client.client.get_place.call_args[1]
            assert call_args["request"]["name"] == f"places/{place_id}"

    def test_get_place_not_found(self, places_client):
        """Test get place when place is not found."""
        places_client.client.get_place.side_effect = gexc.NotFound("Place not found")
        
        result = places_client.get("nonexistent-place-id")
        
        assert result is None

    def test_get_place_invalid_argument_error(self, places_client):
        """Test get place with invalid argument error."""
        places_client.client.get_place.side_effect = gexc.InvalidArgument("Invalid place ID")
        
        with pytest.raises(BookalimoError, match="Google Places Get Place invalid argument"):
            places_client.get("invalid-place-id")

    def test_geocode_success(self, places_client):
        """Test successful geocoding request."""
        request = models.GeocodingRequest(
            address="123 Main St, New York, NY",
            api_key="test-key"
        )
        
        expected_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "123 Main St, New York, NY 10001, USA",
                    "geometry": {
                        "location": {"lat": 40.7128, "lng": -74.0060}
                    }
                }
            ]
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
        request = models.GeocodingRequest(
            address="Test Address",
            api_key="test-key"
        )
        
        places_client.http_client.get.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=Mock()
        )
        
        with pytest.raises(BookalimoError, match="HTTP geocoding failed"):
            places_client.geocode(request)


@pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
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
            client = AsyncGooglePlaces(client=mock_places_client, http_client=mock_http_client)
            return client

    @pytest.mark.asyncio
    async def test_init_with_api_key(self):
        """Test async initialization with API key."""
        with patch("bookalimo.integrations.google_places.client_async.PlacesAsyncClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = AsyncGooglePlaces(api_key="async-test-key-123")
            
            assert client.client is mock_client
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
        places_client.client.transport.close = Mock()
        places_client.http_client.aclose = AsyncMock()
        
        await places_client.aclose()
        
        places_client.client.transport.close.assert_called_once()
        places_client.http_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_autocomplete_success(self, places_client):
        """Test successful async autocomplete request."""
        request = models.AutocompletePlacesRequest(
            input="Empire State Building",
            location_bias=None
        )
        
        # Mock async response
        mock_proto_response = Mock()
        places_client.client.autocomplete_places = AsyncMock(return_value=mock_proto_response)
        
        with patch("bookalimo.integrations.google_places.client_async.validate_proto_to_model") as mock_validate:
            expected_response = models.AutocompletePlacesResponse(
                suggestions=[
                    models.AutocompletePlacesSuggestion(
                        place_id="async-place-id",
                        text="Empire State Building"
                    )
                ]
            )
            mock_validate.return_value = expected_response
            
            result = await places_client.autocomplete(request)
            
            assert result == expected_response
            places_client.client.autocomplete_places.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_success(self, places_client):
        """Test successful async text search."""
        mock_proto_response = Mock()
        mock_proto_response.places = [Mock()]
        places_client.client.search_text = AsyncMock(return_value=mock_proto_response)
        
        with patch("bookalimo.integrations.google_places.client_async.validate_proto_to_model") as mock_validate:
            mock_place = models.Place(
                id="async-place-id",
                display_name="Async Test Place"
            )
            mock_validate.return_value = mock_place
            
            result = await places_client.search("Async Test Query")
            
            assert len(result) == 1
            assert result[0] == mock_place
            places_client.client.search_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_place_success(self, places_client):
        """Test successful async get place request."""
        place_id = "async-test-place-id"
        mock_proto_response = Mock()
        places_client.client.get_place = AsyncMock(return_value=mock_proto_response)
        
        with patch("bookalimo.integrations.google_places.client_async.validate_proto_to_model") as mock_validate:
            expected_place = models.Place(
                id=place_id,
                display_name="Async Test Place"
            )
            mock_validate.return_value = expected_place
            
            result = await places_client.get(place_id)
            
            assert result == expected_place
            places_client.client.get_place.assert_called_once()

    @pytest.mark.asyncio
    async def test_geocode_success(self, places_client):
        """Test successful async geocoding request."""
        request = models.GeocodingRequest(
            address="123 Async St, New York, NY",
            api_key="async-test-key"
        )
        
        expected_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "123 Async St, New York, NY 10001, USA",
                    "geometry": {
                        "location": {"lat": 40.7128, "lng": -74.0060}
                    }
                }
            ]
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
        request = models.GeocodingRequest(
            address="Async Test Address",
            api_key="async-test-key"
        )
        
        places_client.http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Bad Request", request=Mock(), response=Mock())
        )
        
        with pytest.raises(BookalimoError, match="HTTP geocoding failed"):
            await places_client.geocode(request)


class TestGooglePlacesIntegration:
    """Integration tests for Google Places (when available)."""

    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
    def test_real_api_search(self):
        """Test real API search (requires valid API key)."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key or api_key == "test-google-places-key":
            pytest.skip("Real Google Places API key required for integration test")
        
        client = GooglePlaces(api_key=api_key)
        
        try:
            # Search for a well-known location
            results = client.search("Empire State Building New York")
            
            assert isinstance(results, list)
            if results:  # API returned results
                assert all(isinstance(place, models.Place) for place in results)
                # Check that at least one result contains relevant information
                assert any("empire" in place.display_name.lower() for place in results if place.display_name)
        except BookalimoError as e:
            # If API call fails, skip the test
            pytest.skip(f"Google Places API call failed: {e}")
        finally:
            client.close()

    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
    @pytest.mark.asyncio
    async def test_real_api_search_async(self):
        """Test real async API search (requires valid API key)."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key or api_key == "test-google-places-key":
            pytest.skip("Real Google Places API key required for integration test")
        
        async with AsyncGooglePlaces(api_key=api_key) as client:
            try:
                # Search for a well-known location
                results = await client.search("Times Square New York")
                
                assert isinstance(results, list)
                if results:  # API returned results
                    assert all(isinstance(place, models.Place) for place in results)
                    # Check that at least one result contains relevant information
                    assert any("times" in place.display_name.lower() for place in results if place.display_name)
            except BookalimoError as e:
                # If API call fails, skip the test
                pytest.skip(f"Google Places API call failed: {e}")

    @pytest.mark.integration
    @pytest.mark.network
    @pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
    def test_real_geocoding_api(self):
        """Test real geocoding API (requires valid API key)."""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key or api_key == "test-google-places-key":
            pytest.skip("Real Google Places API key required for integration test")
        
        with GooglePlaces(api_key=api_key) as client:
            try:
                request = models.GeocodingRequest(
                    address="1600 Amphitheatre Parkway, Mountain View, CA",
                    api_key=api_key
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
                pytest.skip(f"Geocoding API call failed: {e}")


class TestGooglePlacesErrorHandling:
    """Tests for error handling in Google Places integration."""

    @pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
    def test_handles_quota_exceeded_error(self):
        """Test handling of quota exceeded errors."""
        mock_client = Mock()
        mock_client.search_text.side_effect = gexc.ResourceExhausted("Quota exceeded")
        
        places_client = GooglePlaces(client=mock_client)
        
        with pytest.raises(BookalimoError, match="Google Places Text Search failed"):
            places_client.search("Test Query")

    @pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
    def test_handles_permission_denied_error(self):
        """Test handling of permission denied errors."""
        mock_client = Mock()
        mock_client.autocomplete_places.side_effect = gexc.PermissionDenied("API key invalid")
        
        places_client = GooglePlaces(client=mock_client)
        
        request = models.AutocompletePlacesRequest(
            input="Test Query",
            location_bias=None
        )
        
        with pytest.raises(BookalimoError, match="Google Places Autocomplete failed"):
            places_client.autocomplete(request)

    @pytest.mark.skipif(not PLACES_AVAILABLE, reason="Google Places integration not available")
    def test_handles_network_timeout(self):
        """Test handling of network timeouts in HTTP requests."""
        mock_http_client = Mock()
        mock_http_client.get.side_effect = httpx.TimeoutException("Request timeout")
        
        places_client = GooglePlaces(
            api_key="test-key",
            http_client=mock_http_client
        )
        
        request = models.GeocodingRequest(
            address="Test Address",
            api_key="test-key"
        )
        
        with pytest.raises(BookalimoError, match="HTTP geocoding failed"):
            places_client.geocode(request)