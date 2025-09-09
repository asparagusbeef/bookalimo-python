# Google Places Integration

Use Google Places API for location search, address validation, and airport resolution.

## Setup

```bash
pip install bookalimo[places]
```

Provide your Google Places API key:

```python
# Via constructor
client = AsyncBookalimo(
    credentials=creds,
    google_places_api_key="YOUR_GOOGLE_PLACES_KEY",
)

# Or via environment variable
import os

os.environ["GOOGLE_PLACES_API_KEY"] = "YOUR_KEY"
client = AsyncBookalimo(credentials=creds)
```

## Basic Usage

```python
async with AsyncBookalimo(
    credentials=creds,
    google_places_api_key="YOUR_KEY",
) as client:
    # Search for places
    places = await client.places.search("Empire State Building")
    top_result = places[0]

    # Get detailed place info
    place = await client.places.get(place_id=top_result.google_place.id)

    # Autocomplete for user input
    suggestions = await client.places.autocomplete(input="Empire State")

    # Geocode addresses
    from bookalimo.schemas.places import (
        GeocodingRequest,
    )

    geo = await client.places.geocode(
        GeocodingRequest(address="350 5th Ave, New York")
    )

    # Resolve airports with confidence scoring
    airports = await client.places.resolve_airport(
        query="JFK",
        max_results=3,
        confidence_threshold=0.8,
        text_weight=0.7,  # Blend text (70%) + proximity (30%)
    )
```

## Complete Booking Flow with Geocoding

Here's how to use geocoding for address validation in a real booking scenario:

```python
async with AsyncBookalimo(
    credentials=creds,
    google_places_api_key="YOUR_KEY",
) as client:
    from bookalimo.schemas.places import (
        GeocodingRequest,
    )
    from bookalimo.schemas.booking import (
        RateType,
        Location,
        LocationType,
        Address,
    )

    # Step 1: Autocomplete to find place - user enters "Hilton Cabana"
    autocomplete_results = await client.places.autocomplete(
        input="Hilton Cabana"
    )
    top_suggestion = autocomplete_results.suggestions[
        0
    ].place_prediction

    # Step 2: Geocode the selected place for precise coordinates
    geocode_result = await client.places.geocode(
        GeocodingRequest(place_id=top_suggestion.place_id)
    )

    # Step 3: Extract geocode data (use results[0], not entire response)
    geocode_data = geocode_result["results"][0]

    # Step 4: Create pickup location with geocoded data
    pickup = Location(
        type=LocationType.ADDRESS,
        address=Address(
            google_geocode=geocode_data,  # Precise coordinates + address components
            place_name=top_suggestion.text.text,  # Display name from autocomplete
        ),
    )

    # Airport dropoff (no geocoding needed for airports)
    from bookalimo.schemas.booking import (
        Airport,
    )

    dropoff = Location(
        type=LocationType.AIRPORT,
        airport=Airport(
            iata_code="JFK"
        ),  # 3-letter IATA code - validated
    )

    # Get pricing with geocoded pickup
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,  # Point-to-point booking
        date_time="12/25/2024 03:00 PM",  # MM/dd/yyyy hh:mm tt format
        pickup=pickup,
        dropoff=dropoff,
        passengers=2,  # Min 1, validated
        luggage=2,  # Min 0, validated
    )

    # Complete booking
    booking = await client.reservations.book(
        token=quote.token,
        method="charge",
    )
    print(f"Booking confirmed: {booking.reservation_id}")
```

## Airport Resolution

The `resolve_airport()` method provides intelligent airport matching:

```python
# Find airports by text
airports = await client.places.resolve_airport(
    query="kennedy airport new york",
)

# Or resolve from existing place
place_result = await client.places.search("Eiffel Tower")
airports = await client.places.resolve_airport(
    places=[place_result[0]],
)

# Results include confidence scores
for airport in airports:
    print(
        f"{airport.name} ({airport.iata_code}) - confidence: {airport.confidence}"
    )
```

### Algorithm Overview

The `resolve_airport()` method combines **text matching** with **proximity scoring** to find relevant airports:

- **Text scoring**: Matches query against airport names, cities, and codes
- **Proximity scoring**: Calculates distance from Google Places results
- **Confidence blend**: Configurable via `text_weight` parameter

### Key Parameters

| Parameter              | Default | Description                                                  |
| ---------------------- | ------- | ------------------------------------------------------------ |
| `query`                | None    | Text query for airport search                                |
| `place_id`             | None    | Google place ID for proximity matching                       |
| `places`               | None    | List of Place objects for proximity matching                 |
| `max_distance_km`      | 200     | Maximum distance filter (km)                                 |
| `max_results`          | 5       | Number of results to return                                  |
| `confidence_threshold` | 0.5     | Minimum confidence cutoff                                    |
| `text_weight`          | 0.5     | Text vs proximity weight (0.0=proximity only, 1.0=text only) |

### Usage Patterns

```python
# Default behavior: 50% text, 50% proximity
airports = await client.places.resolve_airport(query="kennedy airport")

# Proximity-only search (find closest airports to Eiffel Tower)
airports = await client.places.resolve_airport(
    query="eiffel tower",
    text_weight=0.0,  # Pure proximity
)

# Mixed scoring (blend text + proximity)
airports = await client.places.resolve_airport(
    query="paris airport",
    text_weight=0.7,  # 70% text, 30% proximity
)

# API cost optimization (use existing Place objects)
eiffel_places = await client.places.search("Eiffel Tower")
airports = await client.places.resolve_airport(
    places=eiffel_places,
    text_weight=0.0,  # Skip additional API call
)
```


## Field Masks

Control response size and cost with field masks. The SDK provides ergonomic field path construction.

### Basic Field Masks

```python
# Default fields: display_name, formatted_address, location
places = await client.places.search("restaurants")

# String list
places = await client.places.search(
    "restaurants",
    fields=[
        "display_name",
        "rating",
        "formatted_address",
    ],
)

# Comma-separated string
places = await client.places.search(
    "restaurants",
    fields="display_name,rating",
)

# All fields (expensive)
places = await client.places.search("restaurants", fields="*")
```

### Ergonomic F Object

Use the `F` object for type-safe field paths:

```python
from bookalimo.schemas.places import (
    F,
)

# Basic fields
places = await client.places.search(
    "restaurants",
    fields=[
        F.display_name,
        F.formatted_address,
        F.rating,
    ],
)

# Nested fields
places = await client.places.search(
    "restaurants",
    fields=[
        F.reviews.text,
        F.reviews.rating,
        F.photos.name,
    ],
)

# Complex nested paths
places = await client.places.search(
    "hotels",
    fields=[
        F.display_name,
        F.photos.author_attributions.display_name,
        F.address_components.long_text,
    ],
)
```

### Field Mask Input Flexibility

`compile_field_mask()` accepts multiple input formats for maximum flexibility:

```python
from bookalimo.schemas.places import (
    compile_field_mask,
    F,
    FieldPath,
)

# String formats
fields = "display_name,formatted_address,rating"  # Comma-separated
fields = [
    "display_name",
    "rating",
]  # List of strings
fields = "display_name"  # Single field

# Object formats
fields = [
    F.display_name,
    F.rating,
]  # F objects
fields = [
    FieldPath("display_name"),
    FieldPath("reviews.text"),
]  # FieldPath objects
fields = [
    F.display_name,
    "rating",
    FieldPath("location"),
]  # Mixed formats
```

### Advanced Field Mask Compilation

> **Note:** The `bookalimo.schemas.places.GooglePlace` model doesn't cover 100% of the Google Places API `Place` object. For custom fields beyond the default schema, use the options below.

```python
from bookalimo.schemas.places import (
    compile_field_mask,
    build_field_tree,
)

# Allow extra fields not in the model
compiled = compile_field_mask(
    [
        F.display_name,
        "custom_business_field",
    ],  # custom_business_field not in GooglePlace
    extra_allowed_fields=["custom_business_field"],
)


# Custom validation with field tree for extended models
class ExtendedGooglePlace(GooglePlace):
    custom_business_field: Optional[str] = None
    special_rating: Optional[float] = None


custom_tree = build_field_tree(ExtendedGooglePlace)
compiled = compile_field_mask(
    [
        F.display_name,
        "custom_business_field",
        "special_rating",
    ],
    field_tree=custom_tree,
)

# Validation with warning handling
compiled = compile_field_mask(
    [
        F.display_name,
        "unknown_field",
    ],
    prefix="places",
    on_warning=lambda msg, path, seg: print(
        f"Field warning: {msg}"
    ),  # msg = "Unknown field 'invalid_field' at 'places.valid1.valid2'", path = "places.valid1.valid2.invalid_field", seg = "invalid_field"
)
```


## Advanced Search Options

### SearchTextRequest

For complex search requirements:

```python
from bookalimo.schemas.places import (
    SearchTextRequest,
    RankPreference,
    LocationBias,
    Circle,
    LatLng,
    PriceLevel,
)

request = SearchTextRequest(
    text_query="restaurants near Times Square",
    included_type="restaurant",
    open_now=True,
    min_rating=4.0,
    max_result_count=10,
    price_levels=[PriceLevel.PRICE_LEVEL_MODERATE],
    rank_preference=RankPreference.RELEVANCE,
    location_bias=LocationBias(
        circle=Circle(
            center=LatLng(
                latitude=40.7580,
                longitude=-73.9855,
            ),
            radius_meters=500,
        )
    ),
)

results = await client.places.search(request=request)
```

### AutocompletePlacesRequest

For autocomplete with filters:

```python
from bookalimo.schemas.places import (
    AutocompletePlacesRequest,
    LocationBias,
)

request = AutocompletePlacesRequest(
    input="Empire State",
    included_primary_types=["tourist_attraction"],
    location_bias=LocationBias(circle=Circle(...)),
    language_code="en-US",
    session_token="billing_session_token",
)

suggestions = await client.places.autocomplete(request=request)
```
