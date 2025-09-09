# Base Models

Foundation models providing automatic field conversion and serialization for Bookalimo API objects.

## Model Architecture

Bookalimo uses a three-tier model architecture for optimal developer experience:

- **`RequestModel`** - For API requests (serializes to `camelCase`)
- **`ResponseModel`** - For API responses (serializes to `snake_case`)
- **`SharedModel`** - Base for shared field definitions (no serialization opinion)

This ensures:
- **API Compatibility** - Request models use the camelCase the API expects
- **Python DX** - Response models use the snake_case Python developers prefer
- **Type Safety** - Clear distinction between request and response contexts

### Request vs Response Serialization

Models have different default serialization based on context:

```python
from bookalimo.schemas import PriceRequest, PriceResponse, RateType

# Request model - serializes to camelCase for API
request = PriceRequest(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    car_class_code="SD",
)

request_data = request.model_dump()
# → {"rateType": 0, "dateTime": "12/25/2024 03:00 PM", "carClassCode": "SD"}

# Response model - serializes to snake_case for Python
response = PriceResponse(token="abc123", prices=[])
response_data = response.model_dump()
# → {"token": "abc123", "prices": []}

# Both accept camelCase and snake_case on input:
request = PriceRequest(
    rateType=RateType.P2P, dateTime="12/25/2024 03:00 PM"
)
request = PriceRequest(
    rate_type=RateType.P2P, date_time="12/25/2024 03:00 PM"
)
```

### Serialization Contexts

Override default serialization using `context` parameter:

```python
from bookalimo.schemas import PriceRequest, CarClassPrice, RateType

# Request model defaults to camelCase, can override to snake_case
request = PriceRequest(
    rate_type=RateType.P2P, date_time="12/25/2024 03:00 PM"
)
data = request.model_dump()  # Default camelCase
# → {"rateType": 0, "dateTime": "12/25/2024 03:00 PM"}

data = request.model_dump(
    context={"case": "snake"}
)  # Override to snake_case
# → {"rate_type": 0, "date_time": "12/25/2024 03:00 PM"}

# Response model defaults to snake_case, can override to camelCase
price = CarClassPrice(
    car_class="SEDAN",
    car_description="Standard",
    max_passengers=4,
    max_luggage=2,
    price=150.0,
    price_default=175.0,
    image_128="img.jpg",
    image_256="img.jpg",
    image_512="img.jpg",
)
data = price.model_dump()  # Default snake_case
# → {"car_class": "SEDAN", "car_description": "Standard", ...}

data = price.model_dump(
    context={"case": "camel"}
)  # Override to camelCase
# → {"carClass": "SEDAN", "carDescription": "Standard", ...}

# Enum output control (same for request and response)
data = request.model_dump(context={"enum_out": "name"})
# → {"rateType": "P2P", "dateTime": "12/25/2024 03:00 PM"}
```

### Context Options

- `enum_out`: `"value"` (default) or `"name"`
- `case`: `"camel"` (default) or `"snake"`
- `snake_case`: `True`/`False` (alias for `case`)

### Usage Patterns

**API Requests** (automatic camelCase):
```python
# SDK handles request serialization internally
quote = await client.pricing.quote(
    rate_type=RateType.P2P,  # Automatically serialized to camelCase for API
    pickup=location,  # Nested models also converted to camelCase
)
```

**Response Handling** (automatic snake_case):
```python
# SDK response models use snake_case by default (better Python DX)
quote = await client.pricing.quote(...)
print(f"Token: {quote.token}")  # Direct property access
data = (
    quote.model_dump()
)  # → {"token": "...", "prices": [...]} (snake_case)
```

**Custom Serialization**:
```python
# Override defaults when needed
request_data = price_request.model_dump(context={"case": "snake"})
response_data = price_response.model_dump(context={"case": "camel"})
debug_data = response.model_dump(context={"enum_out": "name"})
```

## Important Notes

- **Request vs Response**: Use appropriate model variant for your use case
- **Automatic behavior**: Request models → camelCase, Response models → snake_case
- **Google Places models**: Use standard Pydantic serialization (no automatic conversion)
- **Unknown fields**: Ignored during deserialization (API evolution safety)
- **Type safety**: Request and response models are distinct types for better IDE support
