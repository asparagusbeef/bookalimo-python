# Base Models

Foundation models providing automatic field conversion and serialization for Bookalimo API objects.

## ApiModel

All Bookalimo API models inherit from `ApiModel`, which provides:

- **Automatic field conversion** - Python `snake_case` ↔ API `camelCase`
- **Flexible input** - accepts both naming conventions
- **Configurable serialization** - control enum and case output

### Field Name Conversion

Models automatically handle field name conversion:

```python
from bookalimo.schemas.booking import PriceRequest, RateType

# Python snake_case (natural)
request = PriceRequest(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    car_class_code="SD",
    # ...
)

# API camelCase also accepted on input:
request = PriceRequest(
    rateType=RateType.P2P,
    dateTime="12/25/2024 03:00 PM",
    carClassCode="SD",
    # ...
)

# Output uses camelCase by default:
data = request.model_dump()
# → {"rateType": 0, "dateTime": "12/25/2024 03:00 PM", "carClassCode": "SD", ...}
```

### Serialization Contexts

Control output format using `context` parameter:

```python
# Default: enums by value, camelCase fields
data = request.model_dump()
# → {"rateType": 0, "dateTime": "...", "carClassCode": "SD"}

# Enums by name
data = request.model_dump(context={"enum_out": "name"})
# → {"rateType": "P2P", "dateTime": "...", "carClassCode": "SD"}

# snake_case fields
data = request.model_dump(context={"case": "snake"})
# → {"rate_type": 0, "date_time": "...", "car_class_code": "SD"}

# Combined options
data = request.model_dump(context={"enum_out": "name", "case": "snake"})
# → {"rate_type": "P2P", "date_time": "...", "car_class_code": "SD"}

# Boolean alias for case
data = request.model_dump(context={"snake_case": True})
# → {"rate_type": 0, "date_time": "...", "car_class_code": "SD"}
```

### Context Options

- `enum_out`: `"value"` (default) or `"name"`
- `case`: `"camel"` (default) or `"snake"`
- `snake_case`: `True`/`False` (alias for `case`)

### Usage Patterns

**API Requests** (automatic):
```python
# SDK handles serialization internally
quote = await client.pricing.quote(
    rate_type=RateType.P2P,  # Automatically serialized
    pickup=location,  # Automatically converted to camelCase
    # ...
)
```

**Custom Serialization**:
```python
# For logging or external APIs
request_data = price_request.model_dump(
    context={"enum_out": "name", "snake_case": True}
)

# For debugging
debug_data = response.model_dump(context={"enum_out": "name"})
print(f"Rate type: {debug_data['rateType']}")  # "P2P" instead of 0
```

## Important Notes

- **Bookalimo models only**: This applies to `bookalimo.schemas.booking.*` models
- **Google Places models**: Use standard Pydantic serialization (no automatic conversion)
- **Unknown fields**: Ignored during deserialization (API evolution safety)
