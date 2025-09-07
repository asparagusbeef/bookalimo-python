# HTTP Clients

Concrete HTTP transport implementations using httpx for both synchronous and asynchronous operations.

## AsyncTransport

::: bookalimo.transport.httpx_async.AsyncTransport

Asynchronous HTTP transport implementation using httpx.AsyncClient.

### Features

- **Async/await support**: Native asyncio integration
- **Automatic retry**: Exponential backoff with jitter for transient failures  
- **Request correlation**: Unique request IDs for debugging
- **Resource management**: Automatic client lifecycle management
- **Context manager**: Async context manager support

### Configuration

```python
transport = AsyncTransport(
    base_url="https://api.bookalimo.com",
    timeouts=httpx.Timeout(5.0),
    user_agent="my-app/1.0.0",
    credentials=credentials,
    retries=3,
    backoff=0.5
)
```

### Client Management

The transport manages httpx.AsyncClient lifecycle:

- **Auto-creation**: Creates client if none provided
- **Ownership tracking**: Only closes clients it owns
- **Custom clients**: Accepts pre-configured httpx.AsyncClient

```python
# Auto-managed client
async with AsyncTransport() as transport:
    response = await transport.post(...)

# Custom client  
async with httpx.AsyncClient(timeout=10.0) as client:
    transport = AsyncTransport(client=client)
    response = await transport.post(...)
```

### Request Processing

Each request follows this flow:

1. **URL normalization**: Ensures proper path format
2. **Data preparation**: Converts models to JSON
3. **Credential injection**: Adds authentication if provided
4. **Retry execution**: Exponential backoff on failures
5. **Error handling**: Maps exceptions to SDK errors
6. **Response parsing**: Validates and deserializes JSON

### Error Recovery

Automatic retry for:
- **Network errors**: Connection failures, timeouts
- **Transient HTTP errors**: 500, 502, 503, 504 status codes
- **Configuration**: Configurable retry count and backoff

```python
# Custom retry configuration
transport = AsyncTransport(
    retries=5,         # Maximum 5 retry attempts
    backoff=1.0        # Base backoff of 1 second
)
```

### Logging Integration

Emits structured debug logs:

```python
import logging
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

# Logs show:
# → [abc12345] POST /booking/price/ body_keys=['dateTime', 'pickup', ...]
# ← [abc12345] 200 /booking/price/ in 156.2 ms len=2048 reqid=req-server-id
```

### Context Manager Usage

```python
# Recommended pattern
async with AsyncTransport(credentials=creds) as transport:
    pricing_service = AsyncPricingService(transport)
    quote = await pricing_service.quote(...)
    # Transport automatically closed
```

## SyncTransport

::: bookalimo.transport.httpx_sync.SyncTransport

Synchronous HTTP transport implementation using httpx.Client.

### Features

- **Blocking operations**: Standard synchronous I/O
- **Identical API**: Same interface as AsyncTransport
- **Thread-safe**: Safe for multi-threaded usage
- **Resource management**: Automatic client lifecycle

### Configuration

Identical to AsyncTransport but uses synchronous client:

```python
transport = SyncTransport(
    base_url="https://api.bookalimo.com",
    credentials=credentials,
    retries=2,
    backoff=0.3
)
```

### Client Management

Uses httpx.Client with same ownership model:

```python
# Auto-managed client
with SyncTransport() as transport:
    response = transport.post(...)

# Custom client
with httpx.Client(timeout=30.0) as client:
    transport = SyncTransport(client=client)
    response = transport.post(...)
```

### Performance Characteristics

- **Lower overhead**: No async machinery
- **Blocking I/O**: Suitable for sequential operations
- **Thread compatibility**: Use with threading for concurrency

### Usage Pattern

```python
# Basic usage
with SyncTransport(credentials=creds) as transport:
    pricing_service = PricingService(transport)
    quote = pricing_service.quote(...)
```

## Retry Logic

Both implementations use sophisticated retry logic with exponential backoff.

### Retryable Conditions

**Network Errors:**
- `httpx.TimeoutException`
- `httpx.ConnectError`  
- `httpx.ReadTimeout`
- `ConnectionError`

**HTTP Status Codes:**
- `500` - Internal Server Error
- `502` - Bad Gateway  
- `503` - Service Unavailable
- `504` - Gateway Timeout

### Backoff Algorithm

::: bookalimo.transport.retry.calculate_backoff

Exponential backoff with jitter:

- Base delay: `backoff * (2 ^ attempt)`
- Jitter: ±25% randomization to prevent thundering herd
- Minimum delay: 100ms floor
- Maximum attempts: Configurable (default: 2)

```python
# Retry attempts with 0.3s base backoff:
# Attempt 1: ~300ms (±75ms jitter)
# Attempt 2: ~600ms (±150ms jitter)  
# Attempt 3: ~1200ms (±300ms jitter)
```

### Retry Functions

::: bookalimo.transport.retry.async_retry
::: bookalimo.transport.retry.sync_retry

Generic retry functions supporting:
- **Custom predicates**: Configurable retry conditions
- **Exception preservation**: Original exception re-raised on failure
- **Attempt tracking**: Proper backoff calculation

## Error Handling

### HTTP Error Processing

::: bookalimo.transport.utils.handle_http_error

Maps HTTP status codes to appropriate exceptions:

- **408**: `BookalimoTimeout`
- **502, 503, 504**: `BookalimoHTTPError` with service unavailable context
- **Other 4xx/5xx**: Generic `BookalimoHTTPError` with payload

### API Error Processing  

::: bookalimo.transport.utils.handle_api_errors

Handles API-level error responses:

- **Error field**: Responses with `{"error": "message"}`
- **Success flag**: Responses with `{"success": false, "error": "message"}`
- **Structured errors**: Preserves error context from API

### Exception Mapping

Network and HTTP exceptions are mapped to SDK-specific errors:

```python
httpx.TimeoutException → BookalimoTimeout
httpx.ConnectError → BookalimoConnectionError  
httpx.RequestError → BookalimoRequestError
httpx.HTTPStatusError → BookalimoHTTPError
```

## Performance Considerations

### Async vs Sync Selection

**Choose AsyncTransport for:**
- High concurrency requirements
- I/O-bound applications
- Modern async codebases
- Long-running services

**Choose SyncTransport for:**
- Simple sequential operations
- Legacy synchronous codebases  
- Command-line tools
- Testing scenarios

### Resource Management

Both transports properly manage resources:

- **Connection pooling**: httpx handles connection reuse
- **Timeout management**: Configurable request timeouts
- **Memory efficiency**: Streaming response handling
- **Cleanup**: Automatic resource cleanup on context exit

### Connection Configuration

```python
# Custom timeout configuration
timeout = httpx.Timeout(
    connect=5.0,    # Connection timeout
    read=10.0,      # Read timeout  
    write=5.0,      # Write timeout
    pool=2.0        # Pool acquisition timeout
)

transport = AsyncTransport(timeouts=timeout)
```