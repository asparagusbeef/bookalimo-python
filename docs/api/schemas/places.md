# Places Schemas

Data models for Google Places API integration.

## Core Models

- `Place` - structured place result with lat/lng and place type
- `GooglePlace` - raw Google Places API response
- `ResolvedAirport` - airport resolution result with confidence scoring

## Request Models

- `AutocompletePlacesRequest` - autocomplete search parameters
- `SearchTextRequest` - text search with filters and constraints
- `GetPlaceRequest` - place details by ID
- `GeocodingRequest` - forward/reverse geocoding

## Response Models

- `AutocompletePlacesResponse` - autocomplete suggestions
- `SearchTextResponse` - text search results

## Field Masks

Control response data with `FieldMaskInput`:
```python
# String or list of strings
fields = ["display_name", "formatted_address", "rating"]

# Use compile_field_mask for validation
from bookalimo.schemas.places import compile_field_mask

compiled = compile_field_mask(fields)
```
