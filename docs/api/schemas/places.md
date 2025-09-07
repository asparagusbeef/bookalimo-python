# Places Models

Pydantic models for Google Places API integration, providing location search and geocoding capabilities.

## Core Types

### PlaceType

::: bookalimo.schemas.places.PlaceType

Constants for common place types:

- `ADDRESS = "address"` - Street addresses
- `AIRPORT = "airport"` - Airport locations  
- `POI = "poi"` - Points of interest

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

## Place Results

### Place

::: bookalimo.schemas.places.Place

Structured place result from Google Places API searches.

**Key Fields:**
- `formatted_address`: Full formatted address string
- `lat`/`lng`: Geographic coordinates
- `place_type`: Type classification (address, airport, poi)
- `iata_code`: Airport code if applicable
- `google_place`: Raw Google Places API response

**Computed Properties:**
- `country_code`: ISO 3166-1 alpha-2 country code extracted from Google Places data

### GooglePlace

::: bookalimo.schemas.places.place.Place

Comprehensive Google Places API response model with extensive place details.

**Core Identity:**
- `name`: Resource name (`places/{place_id}`)
- `id`: Place ID
- `display_name`: Localized place name
- `types`: Place type classifications

**Location Data:**
- `formatted_address`: Full formatted address
- `address_components`: Structured address components
- `location`: Geographic coordinates
- `viewport`: Recommended map viewport

**Business Information:**
- `rating`: User rating (1.0-5.0)
- `user_rating_count`: Number of reviews
- `price_level`: Price range indicator
- `business_status`: Operational status

**Rich Attributes:**
- `photos`: Place photos (max 10)
- `reviews`: User reviews (max 5)
- `opening_hours`: Operating hours
- `accessibility_options`: Accessibility features
- `payment_options`: Accepted payment methods

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

async with AsyncGooglePlaces(api_key="your-key") as places:
    # Autocomplete search
    results = await places.autocomplete("Empire State Building")
    
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