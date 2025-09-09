# Places Models

Pydantic models for Google Places API integration, providing location search and geocoding capabilities.

## Core Types

### PlaceType

::: bookalimo.schemas.places.PlaceType

String enumeration for common place types:

- `ADDRESS = "address"` - Street addresses
- `AIRPORT = "airport"` - Airport locations
- `POI = "poi"` - Points of interest

### RankPreference

::: bookalimo.schemas.places.RankPreference

String enumeration for ranking preferences in SearchTextRequest:

- `RANK_PREFERENCE_UNSPECIFIED = "RANK_PREFERENCE_UNSPECIFIED"` - Default ranking
- `DISTANCE = "DISTANCE"` - Rank by distance from origin
- `RELEVANCE = "RELEVANCE"` - Rank by search relevance

### EVConnectorType

::: bookalimo.schemas.places.EVConnectorType

String enumeration for electric vehicle connector types:

- `EV_CONNECTOR_TYPE_UNSPECIFIED = "EV_CONNECTOR_TYPE_UNSPECIFIED"` - Unspecified type
- `EV_CONNECTOR_TYPE_OTHER = "EV_CONNECTOR_TYPE_OTHER"` - Other connector type
- `EV_CONNECTOR_TYPE_J1772 = "EV_CONNECTOR_TYPE_J1772"` - J1772 connector
- `EV_CONNECTOR_TYPE_TYPE_2 = "EV_CONNECTOR_TYPE_TYPE_2"` - Type 2 connector
- `EV_CONNECTOR_TYPE_CHADEMO = "EV_CONNECTOR_TYPE_CHADEMO"` - CHAdeMO connector
- `EV_CONNECTOR_TYPE_CCS_COMBO_1 = "EV_CONNECTOR_TYPE_CCS_COMBO_1"` - CCS Combo 1
- `EV_CONNECTOR_TYPE_CCS_COMBO_2 = "EV_CONNECTOR_TYPE_CCS_COMBO_2"` - CCS Combo 2
- `EV_CONNECTOR_TYPE_TESLA = "EV_CONNECTOR_TYPE_TESLA"` - Tesla connector
- `EV_CONNECTOR_TYPE_UNSPECIFIED_GB_T = "EV_CONNECTOR_TYPE_UNSPECIFIED_GB_T"` - GB/T connector
- `EV_CONNECTOR_TYPE_UNSPECIFIED_WALL_OUTLET = "EV_CONNECTOR_TYPE_UNSPECIFIED_WALL_OUTLET"` - Wall outlet

### LatLng

::: bookalimo.schemas.places.common.LatLng

Geographic coordinate representation.

**Validation:**
- `latitude`: Must be in range [-90, 90]
- `longitude`: Must be in range [-180, 180]

### Viewport

::: bookalimo.schemas.places.common.Viewport

Geographic bounding box defined by high and low coordinates.

**Validation:**
- `high.latitude` must be >= `low.latitude`

## Text Formatting

### StringRange

::: bookalimo.schemas.places.StringRange

Defines a substring range within text for highlighting search matches.

**Fields:**
- `start_offset`: Zero-based start position (inclusive)
- `end_offset`: Zero-based end position (exclusive)

**Validation:**
- `start_offset` must be < `end_offset`

### FormattableText

::: bookalimo.schemas.places.FormattableText

Text with optional highlighting ranges for search match emphasis.

**Fields:**
- `text`: The full text string
- `matches`: List of `StringRange` objects indicating highlighted portions

**Validation:**
- Match ranges must be ordered and non-overlapping
- All ranges must be within text bounds

### StructuredFormat

::: bookalimo.schemas.places.StructuredFormat

Structured breakdown of place predictions into main and secondary text components.

**Fields:**
- `main_text`: Primary text (e.g., place name)
- `secondary_text`: Additional context (e.g., city, state)

## Geographic Constraints

### Circle

::: bookalimo.schemas.places.Circle

Circular geographic area defined by center point and radius.

**Fields:**
- `center`: `LatLng` center point
- `radius_meters`: Radius in meters (must be > 0)

### LocationBias

::: bookalimo.schemas.places.LocationBias

Geographic hint to bias search results. Exactly one of `rectangle` or `circle` must be set.

**Usage:**
```python
# Rectangle bias
bias = LocationBias(rectangle=Viewport(high=..., low=...))

# Circle bias
bias = LocationBias(circle=Circle(center=..., radius_meters=1000))
```

### LocationRestriction

::: bookalimo.schemas.places.LocationRestriction

Geographic restriction to limit search results. Exactly one of `rectangle` or `circle` must be set.

Similar to `LocationBias` but enforces hard boundaries rather than preferences.

### SearchTextLocationBias

::: bookalimo.schemas.places.SearchTextLocationBias

Geographic bias specific to SearchTextRequest. Supports both rectangle and circle constraints.

**Usage:**
```python
# Rectangle bias
bias = SearchTextLocationBias(rectangle=Viewport(high=..., low=...))

# Circle bias
bias = SearchTextLocationBias(circle=Circle(center=..., radius_meters=1000))
```

### SearchTextLocationRestriction

::: bookalimo.schemas.places.SearchTextLocationRestriction

Geographic restriction specific to SearchTextRequest. Only supports rectangle constraints.

### EVOptions

::: bookalimo.schemas.places.EVOptions

Electric vehicle charging requirements for place searches.

**Fields:**
- `minimum_charging_rate_kw`: Minimum charging rate in kilowatts
- `connector_types`: List of acceptable EV connector types

### RoutingParameters

::: bookalimo.schemas.places.RoutingParameters

Parameters for routing calculations to search results.

**Fields:**
- `origin`: Explicit routing origin point
- `travel_mode`: Travel mode ("DRIVE", "WALK", "BICYCLE", "TRANSIT")
- `routing_preference`: Routing preference type

## Place Results

### Place

::: bookalimo.schemas.places.Place

Structured place result from Google Places API searches.

**Key Fields:**
- `formatted_address`: Full formatted address string
- `lat`/`lng`: Geographic coordinates
- `place_type`: Type classification (address, airport, poi)
- `google_place`: Raw Google Places API response

**Computed Properties:**
- `country_code`: ISO 3166-1 alpha-2 country code extracted from Google Places data

### GooglePlace

::: bookalimo.schemas.places.GooglePlace

Raw Google Places API response model - Pydantic representation of the google [Place](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places) object.

### Airport

::: bookalimo.schemas.places.Airport

Airport result model with confidence scoring from the resolve_airport functionality.

**Key Fields:**
- `name`: Airport name
- `city`: Airport city location
- `iata_code`: IATA airport code (optional)
- `icao_code`: ICAO airport code (optional)
- `confidence`: Search result confidence score (0.0-1.0)

## Search Requests

### AutocompletePlacesRequest

::: bookalimo.schemas.places.AutocompletePlacesRequest

Request for place autocomplete predictions.

**Required Fields:**
- `input`: Search text (min 1 character)

**Geographic Filtering:**
- `location_bias`: Preference hint (mutually exclusive with `location_restriction`)
- `location_restriction`: Hard geographic boundary
- `included_region_codes`: Limit to specific countries (max 15)

**Type Filtering:**
- `included_primary_types`: Place type filters (max 5)
  - Normal types: `["restaurant", "gas_station"]`
  - Special tokens: `["(regions)"]` or `["(cities)"]` (exclusive)

**Localization:**
- `language_code`: BCP-47 language tag (default: "en-US")
- `region_code`: CLDR region code for localization

**Advanced Options:**
- `origin`: Reference point for distance calculations
- `input_offset`: Cursor position in input text
- `include_query_predictions`: Include non-place suggestions
- `session_token`: Billing session token (base64url, max 36 chars)

**Example:**
```python
request = AutocompletePlacesRequest(
    input="Empire State",
    included_primary_types=["tourist_attraction"],
    location_bias=LocationBias(
        circle=Circle(
            center=LatLng(latitude=40.7128, longitude=-74.0060),
            radius_meters=5000
        )
    ),
    language_code="en-US"
)
```

### GetPlaceRequest

::: bookalimo.schemas.places.GetPlaceRequest

Request for detailed place information by place ID.

**Required Fields:**
- `name`: Resource name format `places/{place_id}`

**Optional Fields:**
- `language_code`: Preferred language (BCP-47)
- `region_code`: Regional preferences (2-letter CLDR)
- `session_token`: Billing session token

**Properties:**
- `place_id`: Extracted place ID from resource name

### SearchTextRequest

::: bookalimo.schemas.places.SearchTextRequest

Request for Google Places Text Search API with comprehensive filtering and localization options.

**Required Fields:**
- `text_query`: Search text string (min 1 character)

**Localization:**
- `language_code`: BCP-47 language tag (e.g., "en-US", "zh-Hant")
- `region_code`: CLDR region code for localization (e.g., "US", "GB")

**Ranking and Filtering:**
- `rank_preference`: How results are ranked ("DISTANCE", "RELEVANCE")
- `included_type`: Single place type filter (e.g., "restaurant", "airport")
- `strict_type_filtering`: Enforce strict type matching

**Result Constraints:**
- `open_now`: Restrict to currently open places
- `min_rating`: Minimum average rating (0.0-5.0, rounded to nearest 0.5)
- `max_result_count`: Maximum results (1-20)
- `price_levels`: List of acceptable price levels

**Geographic Constraints (mutually exclusive):**
- `location_bias`: Geographic hint to bias results
- `location_restriction`: Hard geographic boundaries

**Advanced Options:**
- `ev_options`: Electric vehicle charging requirements
- `routing_parameters`: Routing calculations for distance/time
- `search_along_route_parameters`: Search along a specific route
- `include_pure_service_area_businesses`: Include service businesses without physical locations

**Example:**
```python
request = SearchTextRequest(
    text_query="Italian restaurants",
    included_type="restaurant",
    open_now=True,
    min_rating=4.0,
    max_result_count=10,
    price_levels=[PriceLevel.PRICE_LEVEL_MODERATE],
    rank_preference="RELEVANCE"
)
```

### GeocodingRequest

::: bookalimo.schemas.places.GeocodingRequest

Request for Geocoding API to convert addresses to coordinates.

**Input Options (one required):**
- `address`: Street address or plus code
- `place_id`: Google place ID

**Localization:**
- `language`: Response language
- `region`: Regional bias (ccTLD format)

**URL Generation:**
```python
request = GeocodingRequest(address="1600 Amphitheatre Parkway")
params = request.to_query_params()  # Returns httpx.QueryParams
```

## Search Responses

### SearchTextResponse

::: bookalimo.schemas.places.SearchTextResponse

Response from Google Places Text Search API.

**Fields:**
- `places`: List of `GooglePlace` objects matching the search criteria


### AutocompletePlacesResponse

::: bookalimo.schemas.places.AutocompletePlacesResponse

Ordered list of autocomplete suggestions.

**Fields:**
- `suggestions`: List of `Suggestion` objects

### Suggestion

::: bookalimo.schemas.places.Suggestion

Individual autocomplete suggestion. Exactly one of `place_prediction` or `query_prediction` is set.

### PlacePrediction

::: bookalimo.schemas.places.PlacePrediction

Prediction representing a specific place.

**Key Fields:**
- `place`: Resource name (`places/{place_id}`)
- `place_id`: Place ID string
- `text`: Full prediction text with highlights
- `structured_format`: Broken down main/secondary text
- `types`: Place type classifications
- `distance_meters`: Distance from origin point (if provided)

### QueryPrediction

::: bookalimo.schemas.places.QueryPrediction

Prediction representing a search query rather than a specific place.

**Fields:**
- `text`: Query text with highlights
- `structured_format`: Structured query breakdown

## Integration Usage

### Basic Place Search

```python
from bookalimo.integrations.google_places import AsyncGooglePlaces
from bookalimo.schemas.places import SearchTextRequest, RankPreference

async with AsyncGooglePlaces(api_key="your-key") as places:
    # Simple text search
    results = await places.search("Empire State Building")

    # Advanced search with SearchTextRequest
    search_request = SearchTextRequest(
        text_query="restaurants near Times Square",
        included_type="restaurant",
        open_now=True,
        min_rating=4.0,
        rank_preference=RankPreference.RELEVANCE
    )
    results = await places.search(request=search_request)

    # Autocomplete search
    autocomplete_results = await places.autocomplete("Empire State Building")

    # Get detailed place info
    place = await places.get_place("places/ChIJ...")

    # Geocode address
    geocoded = await places.geocode("1600 Amphitheatre Parkway")
```

### Converting to Bookalimo Location

```python
from bookalimo.schemas.booking import Location, LocationType, Address

# Convert Google place to Bookalimo location
google_place = await places.get_place("places/ChIJ...")

location = Location(
    type=LocationType.ADDRESS,
    address=Address(
        google_geocode=google_place.model_dump(),
        place_name=google_place.display_name.text
    )
)
```

## Validation Features

All places models include comprehensive validation:

- **Format validation**: Place IDs, resource names, coordinates
- **Range validation**: Latitude/longitude bounds, rating ranges
- **Consistency validation**: Place ID matches resource name
- **Length limits**: Photos (10), reviews (5), region codes (15)
- **Regex validation**: BCP-47 language codes, hex colors, place types
- **Mutual exclusion**: Location bias vs restriction
