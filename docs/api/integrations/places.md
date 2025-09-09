# Google Places Integration

Google Places API integration for location search, autocomplete, and geocoding services that seamlessly integrate with Book-A-Limo booking workflows.

## Overview

The Google Places integration provides:

- **Place Autocomplete**: Search suggestions for addresses and points of interest
- **Place Details**: Detailed information about specific locations
- **Text Search**: Find places using natural language queries
- **Geocoding**: Convert addresses to coordinates

All results are automatically formatted for use with Bookalimo booking requests.

## Installation

Install the Google Places integration:

```bash
pip install bookalimo[places]
```

## Authentication

The integration supports multiple authentication methods:

1. **Constructor API Key**
2. **Environment Variable**: `GOOGLE_PLACES_API_KEY`
3. **Google Application Default Credentials** (except for Geocoding API, where ADC is not supported yet)

```python
# Method 1: Direct API key
client = AsyncGooglePlaces(api_key="your-google-places-api-key")

# Method 2: Environment variable
import os
os.environ["GOOGLE_PLACES_API_KEY"] = "your-api-key"
client = AsyncGooglePlaces()

# Method 3: Via Bookalimo client
bookalimo_client = AsyncBookalimo(
    credentials=bookalimo_creds,
    google_places_api_key="your-google-places-api-key"
)
```

## AsyncGooglePlaces

::: bookalimo.integrations.google_places.AsyncGooglePlaces

Asynchronous Google Places client for location services.

### Constructor

```python
client = AsyncGooglePlaces(
    api_key="your-google-places-api-key",
    client=None,  # Optional pre-configured PlacesAsyncClient
    http_client=None  # Optional custom httpx.AsyncClient
)
```

### Context Manager Usage

```python
async with AsyncGooglePlaces(api_key="your-key") as places:
    results = await places.autocomplete(request)
    # Client automatically closed
```

### Methods

#### autocomplete()

Get autocomplete suggestions for location queries.

**Parameters:**
- `input`: The text string on which to search (optional)
- `request`: `AutocompletePlacesRequest` object with search parameters (optional)

**Returns:** `AutocompletePlacesResponse` with place suggestions

**Note:** Either `input` or `request` must be provided. If both are provided, `request` will be used.

**Example:**
```python
from bookalimo.schemas.places import AutocompletePlacesRequest

request = AutocompletePlacesRequest(
    input="Empire State Building",
    language_code="en-US",
    included_primary_types=["tourist_attraction"]
)

response = await places.autocomplete(request)
for suggestion in response.suggestions:
    if suggestion.place_prediction:
        print(suggestion.place_prediction.text.text)
```

#### search()

Search for places using text queries or advanced `SearchTextRequest` objects.

**Parameters:**
- `query`: Simple search text string (optional)
- `request`: `SearchTextRequest` object with advanced parameters (optional)
- `fields`: Optional field mask for response data
- `**kwargs`: Additional search parameters

**Note:** Either `query` or `request` must be provided, but not both.

**Returns:** List of `Place` objects

**Basic Example:**
```python
# Simple text search
results = await places.search("restaurants near Times Square")
for place in results:
    print(f"{place.formatted_address} ({place.place_type})")
```

**Advanced Example with SearchTextRequest:**
```python
from bookalimo.schemas.places import SearchTextRequest, RankPreference, PriceLevel

# Advanced search with filters
search_request = SearchTextRequest(
    text_query="restaurants near Times Square",
    included_type="restaurant",
    open_now=True,
    min_rating=4.0,
    max_result_count=10,
    price_levels=[PriceLevel.PRICE_LEVEL_MODERATE, PriceLevel.PRICE_LEVEL_EXPENSIVE],
    rank_preference=RankPreference.RELEVANCE
)

results = await places.search(request=search_request)
for place in results:
    print(f"{place.formatted_address} - Rating: {place.google_place.rating}")
```

#### resolve_airport()

Resolve airport candidates from text queries, place IDs, or existing Place objects with advanced filtering and confidence scoring.

**Parameters:**
- `query`: Text query for airport search (optional)
- `place_id`: Google place ID to resolve (optional)
- `places`: List of existing Place objects to analyze (optional)
- `max_distance_km`: Maximum distance for proximity matching (default: 100km)
- `max_results`: Maximum number of results to return (default: 5)
- `confidence_threshold`: Minimum confidence threshold (default: 1.0)

**Rules:**
- Provide at most one of `{place_id, places}` - `query` may accompany either
- If only `query` is provided, searches for places first
- If `place_id` is provided, fetches the place and derives query if needed
- If `places` is provided with single place and no query, derives query from place name
- If multiple places provided, query is required for disambiguation

**Returns:** List of `Airport` objects with confidence scores

**Examples:**
```python
# Search by text query
airports = await places.resolve_airport(query="JFK New York")
for airport in airports:
    print(f"{airport.name} ({airport.iata_code}): {airport.confidence}")

# Resolve from place ID
airports = await places.resolve_airport(place_id="ChIJ...")

# Analyze existing places
existing_places = await places.search("airports near NYC")
airports = await places.resolve_airport(
    places=existing_places,
    query="international airport",
    max_distance_km=50,
    max_results=3
)

# Filter by confidence
high_confidence = [
    airport for airport in airports
    if airport.confidence > 0.8
]
```

#### get()

Get detailed information for a specific place.

**Parameters:**
- `place_id`: The ID of the place to retrieve details for.
- `request`: `GetPlaceRequest` object with place resource name
- `fields`: Optional field mask for response data

**Note:** Either `place_id` or `request` must be provided, but not both. If both are provided, `request` will be used.
**Returns:** `Place` object or `None` if not found

**Example:**
```python
from bookalimo.schemas.places import GetPlaceRequest

request = GetPlaceRequest(name="places/ChIJN1t_tDeuEmsRUsoyG83frY4")
place = await places.get(request)

if place:
    print(f"Found: {place.formatted_address}")
```

#### geocode()

Convert addresses to coordinates using Google Geocoding API.

**Parameters:**
- `request`: `GeocodingRequest` object

**Returns:** Raw geocoding response dictionary

**Example:**
```python
from bookalimo.schemas.places import GeocodingRequest

request = GeocodingRequest(address="1600 Amphitheatre Parkway, Mountain View, CA")
result = await places.geocode(request)

if result["status"] == "OK":
    location = result["results"][0]["geometry"]["location"]
    print(f"Coordinates: {location['lat']}, {location['lng']}")
```

## GooglePlaces

::: bookalimo.integrations.google_places.GooglePlaces

Synchronous Google Places client with identical interface.

### Usage

```python
with GooglePlaces(api_key="your-key") as places:
    results = places.search("airports near New York")
    place = places.get(GetPlaceRequest(name="places/ChIJ..."))
    airports = places.resolve_airport(query="JFK airport")
    geocoded = places.geocode(request)
```

## Integration with Bookalimo

### Via Client Properties

Access Google Places through Bookalimo client:

```python
async with AsyncBookalimo(
    credentials=creds,
    google_places_api_key="your-google-places-key"
) as client:
    # Search for pickup location
    pickup_results = await client.places.search("JFK Airport")
    pickup_place = pickup_results[0]

    # Search for destination
    dropoff_results = await client.places.search("Empire State Building")
    dropoff_place = dropoff_results[0]

    # Convert to Bookalimo locations
    pickup_location = create_location_from_place(pickup_place)
    dropoff_location = create_location_from_place(dropoff_place)

    # Get pricing
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup_location,
        dropoff=dropoff_location,
        passengers=2,
        luggage=2
    )
```

### Location Conversion

Convert Google Places results to Bookalimo locations:

```python
from bookalimo.schemas.booking import Location, LocationType, Address, Airport

def create_location_from_place(place):
    """Convert Google Places result to Bookalimo Location."""
    geocode = await client.places.geocode(place.google_place.id)
    if place.place_type == "airport":
        # For airports, you should use resolve_airport() and provide the IATA code to the Airport model.
        airports = await client.places.resolve_airport(place_id=place.google_place.id)
        return Location(
            type=LocationType.AIRPORT,
            address=Airport(
                iata_code=airports[0].iata_code,
                google_geocode=geocode,
                place_name=place.google_place.display_name.text if place.google_place.display_name else place.formatted_address
            )
        )
    else:
        return Location(
            type=LocationType.ADDRESS,
            address=Address(
                google_geocode=geocode,
                place_name=place.google_place.display_name.text if place.google_place.display_name else place.formatted_address
            )
        )

# Usage
places_results = await client.places.search("Central Park")
location = create_location_from_place(places_results[0])
```

## Common Use Cases

### Airport Lookup and Resolution

```python
# Traditional search for airports
airports = await places.search("JFK airport")
lax_results = await places.search("Los Angeles International Airport")

# Advanced airport resolution with confidence scoring
airport_candidates = await places.resolve_airport(
    query="JFK New York international",
    max_distance_km=50,
    max_results=3,
    confidence_threshold=0.8
)

for airport in airport_candidates:
    print(f"{airport.name} ({airport.iata_code})")
    print(f"  Confidence: {airport.confidence}")

# Convert to Bookalimo airport location
if airport_candidates:
    best_match = airport_candidates[0]
    airport_location = Location(
        type=LocationType.AIRPORT,
        airport=Airport(iata_code=best_match.iata_code)
    )
```

### Address Validation

```python
# Validate and standardize addresses
request = AutocompletePlacesRequest(
    input="123 Main Street, New York",
    included_primary_types=["street_address"]
)

suggestions = await places.autocomplete(request)
if suggestions.suggestions:
    # Get detailed place info
    place_pred = suggestions.suggestions[0].place_prediction
    place = await places.get(GetPlaceRequest(name=place_pred.place))

    # Use validated address in booking
    address_location = Location(
        type=LocationType.ADDRESS,
        address=Address(
            google_geocode=place.google_place.model_dump(),
            place_name=place.formatted_address
        )
    )
```

### Point of Interest Search

```python
# Simple text search
pois = await places.search("Empire State Building")

# Advanced search with geographic restrictions
from bookalimo.schemas.places import (
    SearchTextRequest, SearchTextLocationBias, Circle, LatLng
)

restaurant_request = SearchTextRequest(
    text_query="restaurants in Times Square",
    included_type="restaurant",
    location_bias=SearchTextLocationBias(
        circle=Circle(
            center=LatLng(latitude=40.7580, longitude=-73.9855),  # Times Square
            radius_meters=500
        )
    ),
    open_now=True,
    min_rating=4.0
)

restaurants = await places.search(request=restaurant_request)

# Convert to booking locations
poi_location = Location(
    type=LocationType.ADDRESS,
    address=Address(
        google_geocode=pois[0].google_place.model_dump(),
        place_name=pois[0].formatted_address
    )
)
```

### Advanced Text Search

The `SearchTextRequest` model provides comprehensive search capabilities:

```python
from bookalimo.schemas.places import (
    SearchTextRequest, RankPreference, EVOptions, RoutingParameters,
    SearchTextLocationRestriction, Viewport, LatLng, PriceLevel
)

# Complex search with all features
advanced_request = SearchTextRequest(
    text_query="electric vehicle charging stations",
    language_code="en-US",
    region_code="US",
    rank_preference=RankPreference.DISTANCE,
    included_type="gas_station",
    strict_type_filtering=True,
    open_now=True,
    min_rating=3.5,
    max_result_count=15,
    price_levels=[PriceLevel.PRICE_LEVEL_FREE, PriceLevel.PRICE_LEVEL_INEXPENSIVE],

    # Geographic restrictions
    location_restriction=SearchTextLocationRestriction(
        rectangle=Viewport(
            high=LatLng(latitude=40.8, longitude=-73.9),
            low=LatLng(latitude=40.7, longitude=-74.0)
        )
    ),

    # EV-specific options
    ev_options=EVOptions(
        minimum_charging_rate_kw=50.0,
        connector_types=["EV_CONNECTOR_TYPE_CCS_COMBO_1", "EV_CONNECTOR_TYPE_TESLA"]
    ),

    # Routing parameters
    routing_parameters=RoutingParameters(
        origin=LatLng(latitude=40.7128, longitude=-74.0060),
        travel_mode="DRIVE"
    ),

    include_pure_service_area_businesses=False
)

results = await places.search(request=advanced_request)
```

### Autocomplete for User Input

```python
async def get_location_suggestions(user_input: str):
    """Provide autocomplete suggestions for user input."""
    request = AutocompletePlacesRequest(
        input=user_input,
        language_code="en-US",
        included_primary_types=["address", "airport", "tourist_attraction"]
    )

    response = await places.autocomplete(request)
    suggestions = []

    for suggestion in response.suggestions:
        if suggestion.place_prediction:
            pred = suggestion.place_prediction
            suggestions.append({
                "text": pred.text.text,
                "place_id": pred.place_id,
                "types": pred.types
            })

    return suggestions

# Usage in web application
suggestions = await get_location_suggestions("Empire")
# Returns: [{"text": "Empire State Building, New York, NY, USA", ...}]
```

## Error Handling

Google Places operations can fail for various reasons:

```python
from bookalimo.exceptions import BookalimoError

try:
    results = await places.search("nonexistent location query")
except BookalimoError as e:
    print(f"Places API error: {e}")
    # Handle API errors (quota exceeded, invalid key, etc.)

try:
    place = await places.get(GetPlaceRequest(name="invalid-place-id"))
except BookalimoError as e:
    print(f"Get place failed: {e}")
    # Handle invalid place ID or API errors
```

## Best Practices

### API Key Management

```python
import os

# Use environment variables for production
api_key = os.getenv("GOOGLE_PLACES_API_KEY")
if not api_key:
    raise ValueError("Google Places API key not configured")

places = AsyncGooglePlaces(api_key=api_key)
```

### Rate Limiting and Quotas

```python
import asyncio

async def search_with_backoff(places, queries):
    """Search multiple queries with rate limiting."""
    results = []

    for query in queries:
        try:
            result = await places.search(query)
            results.append(result)

            # Add delay to respect rate limits
            await asyncio.sleep(0.1)

        except BookalimoError as e:
            if "quota" in str(e).lower():
                print("Quota exceeded - waiting before retry")
                await asyncio.sleep(60)
                # Retry logic here
            else:
                print(f"Search failed for '{query}': {e}")

    return results
```

### Session Token Usage

For autocomplete → place details workflows, use session tokens for billing efficiency:

```python
import uuid

# Generate session token
session_token = str(uuid.uuid4())[:32]

# Use in autocomplete
request = AutocompletePlacesRequest(
    input="Empire State",
    session_token=session_token
)
suggestions = await places.autocomplete(request)

# Use same token for place details
if suggestions.suggestions:
    place_pred = suggestions.suggestions[0].place_prediction
    place_request = GetPlaceRequest(
        name=place_pred.place,
        session_token=session_token  # Same token for billing
    )
    place = await places.get(place_request)
```

### Caching Results

```python
from functools import lru_cache
from typing import Dict, List

class PlacesCache:
    def __init__(self, places_client):
        self.places = places_client
        self._cache: dict[str, any] = {}

    async def search_cached(self, query: str):
        """Search with simple caching."""
        if query in self._cache:
            return self._cache[query]

        results = await self.places.search(query)
        self._cache[query] = results
        return results

# Usage
cached_places = PlacesCache(places_client)
results = await cached_places.search_cached("JFK Airport")
```

## Field Masks and Performance

Control response size and cost using field masks:

```python
# Minimal fields for autocomplete display
minimal_fields = ["places.display_name", "places.formatted_address"]

# Comprehensive fields for booking
booking_fields = [
    "places.display_name",
    "places.formatted_address",
    "places.location",
    "places.address_components",
    "places.types"
]

# Use appropriate field mask
results = await places.search("restaurants", fields=minimal_fields)
```
