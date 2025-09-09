# Advanced Usage

Advanced configuration and customization patterns.

## Custom Transports

Override transport behavior for specific requirements:

```python
import httpx
from bookalimo import (
    AsyncBookalimo,
)
from bookalimo.transport import (
    AsyncTransport,
)

# Custom transport configuration
custom_transport = AsyncTransport(
    base_url="https://api.bookalimo.com",
    timeouts=httpx.Timeout(
        connect=5.0,
        read=30.0,
        write=5.0,
        pool=2.0,
    ),
    credentials=credentials,
    retries=5,
    backoff=1.0,
)

# Use custom transport
async with AsyncBookalimo(transport=custom_transport) as client:
    quote = await client.pricing.quote(...)
```

## Configuration Constants

Access default configuration from `bookalimo.config`:

```python
from bookalimo.config import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    DEFAULT_RETRIES,
    DEFAULT_BACKOFF,
    DEFAULT_STATUS_FORCELIST,
)

# Use in custom configuration
transport = AsyncTransport(
    base_url=DEFAULT_BASE_URL,
    retries=DEFAULT_RETRIES * 2,  # Double default retries
    backoff=DEFAULT_BACKOFF,
)
```

### Available Constants

- `DEFAULT_BASE_URL` - `"https://www.bookalimo.com/web/api"`
- `DEFAULT_TIMEOUT` - `5.0`
- `DEFAULT_USER_AGENT` - `"bookalimo-python/{version}"`
- `DEFAULT_RETRIES` - `2`
- `DEFAULT_BACKOFF` - `0.3`
- `DEFAULT_STATUS_FORCELIST` - `(500, 502, 503, 504)`

## Logging Configuration

### Environment Variable

```bash
export BOOKALIMO_LOG_LEVEL=DEBUG
```

### Programmatic Setup

```python
import logging
from bookalimo.logging import (
    get_logger,
)

# Configure SDK logging
logging.getLogger("bookalimo").setLevel(logging.DEBUG)

# Or get specific logger
transport_logger = get_logger("transport")
places_logger = get_logger("places")
```

### Debug Logging

Enable debug logging to see request/response details:

```python
import logging

logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

async with AsyncBookalimo(credentials=creds) as client:
    quote = await client.pricing.quote(...)
    # Logs show:
    # → [abc12345] POST /booking/price/ body_keys=['dateTime', 'pickup', ...]
    # ← [abc12345] 200 /booking/price/ in 245.3 ms len=1024
```

## Retry Configuration

Customize retry behavior:

```python
# Aggressive retry for unreliable networks
transport = AsyncTransport(
    retries=10,
    backoff=2.0,
    credentials=credentials,  # 2s, 4s, 8s, 16s...
)

# No retries for testing
test_transport = SyncTransport(
    retries=0,
    timeouts=1.0,
    credentials=test_credentials,
)
```

## Custom HTTP Clients

Inject pre-configured httpx clients:

```python
# Custom httpx client
async with httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100),
) as http_client:
    transport = AsyncTransport(
        client=http_client,
        credentials=credentials,
    )

    async with AsyncBookalimo(transport=transport) as client:
        quote = await client.pricing.quote(...)
```

## Environment Configuration

Production-ready environment setup:

```bash
# .env file
BOOKALIMO_USER_ID=AGENCY123
BOOKALIMO_PASSWORD=secure_password
BOOKALIMO_IS_CUSTOMER=false
BOOKALIMO_LOG_LEVEL=INFO
GOOGLE_PLACES_API_KEY=your_google_key
```

```python
import os
from bookalimo import (
    AsyncBookalimo,
)
from bookalimo.transport.auth import (
    Credentials,
)


def create_production_client():
    credentials = Credentials.create(
        user_id=os.getenv("BOOKALIMO_USER_ID"),
        password=os.getenv("BOOKALIMO_PASSWORD"),
        is_customer=os.getenv(
            "BOOKALIMO_IS_CUSTOMER",
            "false",
        ).lower()
        == "true",
    )

    return AsyncBookalimo(
        credentials=credentials,
        google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY"),
    )
```
