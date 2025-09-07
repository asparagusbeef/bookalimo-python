# Transport Layer

HTTP communication layer providing sync and async interfaces to the Book-A-Limo API with automatic retry, error handling, and authentication injection.

## Architecture

The transport layer is built on a modular architecture:

- **Base Interfaces**: Abstract base classes defining the transport contract
- **HTTP Implementations**: Concrete implementations using httpx for sync and async
- **Authentication**: Credential management and automatic injection
- **Retry Logic**: Exponential backoff with jitter for transient failures
- **Error Handling**: Comprehensive error mapping and context preservation

## Base Interfaces

### BaseTransport

::: bookalimo.transport.base.BaseTransport

Abstract base class for synchronous transport implementations.

**Methods:**
- `post(path, model, response_model)`: Execute POST request with model serialization
- `close()`: Clean up transport resources
- `prepare_data(model)`: Convert Pydantic model to API format

### AsyncBaseTransport  

::: bookalimo.transport.base.AsyncBaseTransport

Abstract base class for asynchronous transport implementations.

**Methods:**
- `post(path, model, response_model)`: Execute async POST request
- `aclose()`: Clean up async transport resources  
- `prepare_data(model)`: Convert Pydantic model to API format

## Data Preparation

Both base classes provide `prepare_data()` method that:

- Converts Pydantic models to JSON-serializable dictionaries
- Excludes `None` values to minimize payload size
- Uses `mode="json"` for proper enum and datetime serialization

```python
# Internal model preparation
data = transport.prepare_data(price_request)
# → {"rateType": 0, "dateTime": "12/25/2024 03:00 PM", ...}
```

## Error Handling

The transport layer provides comprehensive error handling:

### HTTP Status Errors
- **4xx Client Errors**: Mapped to `BookalimoHTTPError` with payload
- **408 Timeout**: Specialized `BookalimoTimeout` exception
- **5xx Server Errors**: Service unavailability errors with retry logic

### Network Errors  
- **Connection Errors**: Mapped to `BookalimoConnectionError`
- **Timeout Errors**: Mapped to `BookalimoTimeout`
- **Request Errors**: General `BookalimoRequestError`

### API-Level Errors
- **Error Responses**: JSON responses with `error` field
- **Success Flag**: Responses with `success: false`
- **Invalid JSON**: Malformed response handling

## Request Flow

1. **URL Construction**: Path normalization and base URL joining
2. **Data Preparation**: Model serialization and credential injection
3. **Request Execution**: HTTP POST with retry logic
4. **Response Validation**: Status code and JSON parsing
5. **Error Handling**: Comprehensive error mapping
6. **Model Parsing**: Response deserialization to Pydantic models

## Usage

Transport instances are typically created by client classes:

```python
# Async transport
transport = AsyncTransport(
    base_url="https://api.bookalimo.com",
    credentials=credentials,
    retries=3,
    backoff=0.5
)

# Execute request
response = await transport.post(
    "/booking/price/",
    price_request,
    PriceResponse
)
```

## Configuration

All transport implementations accept:

- `base_url`: API endpoint base URL (default from config)
- `timeouts`: Request timeout configuration
- `user_agent`: User agent string (includes SDK version)
- `credentials`: Authentication credentials
- `retries`: Maximum retry attempts (default: 2)
- `backoff`: Base backoff delay in seconds (default: 0.3)

## Logging

Transport operations emit structured logs at DEBUG level:

```
→ [a1b2c3d4] POST /booking/price/ body_keys=['dateTime', 'dropoff', 'luggage', 'passengers', 'pickup', 'rateType']
← [a1b2c3d4] 200 /booking/price/ in 245.3 ms len=1024 reqid=req-xyz
```

Log format: `{direction} [{request_id}] {method} {path} {details}`

- **Request**: Shows sanitized body keys (credentials excluded)  
- **Response**: Shows status, duration, content length, server request ID
- **Errors**: Shows error type and details with request context