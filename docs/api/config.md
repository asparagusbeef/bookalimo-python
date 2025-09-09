# Configuration

Default configuration values and constants used throughout the Bookalimo SDK.

## Constants

::: bookalimo.config

### API Configuration

#### DEFAULT_BASE_URL
```python
DEFAULT_BASE_URL = "https://www.bookalimo.com/web/api"
```
Default API endpoint for Book-A-Limo services.

**Usage:**
- Used by transport layers when no custom `base_url` provided
- Can be overridden in client or transport constructors
- Should use HTTPS in production environments

#### DEFAULT_TIMEOUT
```python
DEFAULT_TIMEOUT = 5.0
```
Default request timeout in seconds.

**Usage:**
- Applied to all HTTP operations (connect, read, write)
- Used when no custom timeout configuration provided
- Can be overridden with httpx.Timeout objects for granular control

#### DEFAULT_USER_AGENT
```python
DEFAULT_USER_AGENT = f"bookalimo-python/{__version__}"
```
Default User-Agent header sent with all requests.

**Usage:**
- Identifies SDK version to API servers
- Can be overridden for custom application identification
- Useful for API usage analytics and debugging

### Retry Configuration

#### DEFAULT_RETRIES
```python
DEFAULT_RETRIES = 2
```
Default maximum number of retry attempts for failed requests.

**Behavior:**
- Original request + 2 retries = 3 total attempts maximum
- Applied to transient failures (network errors, 5xx status codes)
- Can be overridden in transport constructors

#### DEFAULT_BACKOFF
```python
DEFAULT_BACKOFF = 0.3
```
Default base backoff delay in seconds for retry attempts.

**Calculation:**
- Uses exponential backoff: `backoff * (2 ^ attempt)`
- Includes ±25% jitter to prevent thundering herd
- Minimum delay of 100ms enforced

**Example timing:**
```
Attempt 1: ~300ms (±75ms jitter)
Attempt 2: ~600ms (±150ms jitter)
```

#### DEFAULT_STATUS_FORCELIST
```python
DEFAULT_STATUS_FORCELIST = (500, 502, 503, 504)
```
HTTP status codes that trigger automatic retries.

**Status Codes:**
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable
- `504` - Gateway Timeout

**Usage:**
- Only these server errors trigger retries
- Client errors (4xx) are not retried
- Used by retry logic in transport layer

### Timeout Configuration

#### DEFAULT_TIMEOUTS
```python
DEFAULT_TIMEOUTS = DEFAULT_TIMEOUT
```
Unified timeout configuration defaulting to `DEFAULT_TIMEOUT`.

**Usage:**
- Can be a simple float for uniform timeouts
- Can be replaced with httpx.Timeout object for granular control

**Examples:**
```python
# Simple timeout
transport = AsyncTransport(timeouts=10.0)

# Granular timeout control
import httpx
transport = AsyncTransport(
    timeouts=httpx.Timeout(
        connect=5.0,    # Connection establishment
        read=30.0,      # Reading response data
        write=5.0,      # Sending request data
        pool=2.0        # Getting connection from pool
    )
)
```

## Configuration Usage

### Environment-Based Configuration

```python
import os
from bookalimo import AsyncBookalimo
from bookalimo.config import DEFAULT_BASE_URL

# Override default values from environment
base_url = os.getenv("BOOKALIMO_API_URL", DEFAULT_BASE_URL)
timeout = float(os.getenv("BOOKALIMO_TIMEOUT", "10.0"))
retries = int(os.getenv("BOOKALIMO_RETRIES", "3"))

client = AsyncBookalimo(
    base_url=base_url,
    timeouts=timeout,
    retries=retries
)
```

### Development Configuration

```python
from bookalimo import AsyncBookalimo
from bookalimo.transport import AsyncTransport
import httpx

# Development transport with relaxed timeouts
dev_transport = AsyncTransport(
    base_url="https://staging.bookalimo.com/web/api",  # Staging environment
    timeouts=httpx.Timeout(30.0),                      # Longer timeouts
    retries=5,                                         # More retries
    backoff=0.1                                        # Faster retries
)

client = AsyncBookalimo(transport=dev_transport)
```

### Production Configuration

```python
from bookalimo import AsyncBookalimo
from bookalimo.config import DEFAULT_BASE_URL
import httpx
import os

# Production-optimized configuration
production_client = AsyncBookalimo(
    credentials=credentials,
    base_url=DEFAULT_BASE_URL,  # Stable production endpoint
    timeouts=httpx.Timeout(
        connect=5.0,    # Quick connection timeout
        read=15.0,      # Reasonable read timeout
        write=5.0,      # Quick write timeout
        pool=2.0        # Fast pool timeout
    ),
    user_agent=f"my-booking-app/{app_version}",
    retries=2,          # Conservative retry count
    backoff=0.5         # Moderate backoff
)
```

### Testing Configuration

```python
from bookalimo import Bookalimo
from bookalimo.transport import SyncTransport
import httpx

# Fast configuration for unit tests
test_transport = SyncTransport(
    base_url="https://test.bookalimo.com",
    timeouts=httpx.Timeout(1.0),  # Fast timeouts
    retries=0,                    # No retries in tests
    user_agent="test-suite/1.0"
)

client = Bookalimo(transport=test_transport)
```

## Customization Examples

### Custom Retry Strategy

```python
from bookalimo.transport import AsyncTransport

# Aggressive retry for unreliable networks
reliable_transport = AsyncTransport(
    retries=10,         # Many retries
    backoff=2.0,        # Longer base backoff
    # Will create delays: ~2s, ~4s, ~8s, ~16s, etc.
)
```

### Custom User Agent

```python
from bookalimo import AsyncBookalimo

# Custom application identification
client = AsyncBookalimo(
    user_agent="MyTravelApp/2.1.0 (support@mytravelapp.com)",
    credentials=credentials
)
```

### Regional Configuration

```python
# European deployment example
eu_client = AsyncBookalimo(
    base_url="https://eu.bookalimo.com/web/api",  # Regional endpoint
    timeouts=httpx.Timeout(10.0),                # Account for latency
    user_agent="EU-TravelPortal/1.0",
    credentials=eu_credentials
)
```

### Load Balancer Configuration

```python
import random
from bookalimo import AsyncBookalimo

# Simple load balancing across endpoints
ENDPOINTS = [
    "https://api1.bookalimo.com/web/api",
    "https://api2.bookalimo.com/web/api",
    "https://api3.bookalimo.com/web/api"
]

def create_client():
    return AsyncBookalimo(
        base_url=random.choice(ENDPOINTS),
        credentials=credentials,
        retries=1  # Lower retries since we can try different endpoints
    )
```

### Debug Configuration

```python
import logging
from bookalimo import AsyncBookalimo

# Enable debug logging to see configuration in use
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

client = AsyncBookalimo(
    credentials=credentials,
    retries=1,      # See retry behavior
    backoff=0.1     # Fast retries for debugging
)

# Logs will show:
# AsyncTransport initialized (base_url=https://www.bookalimo.com/web/api, timeout=5.0, ...)
```

## Configuration Validation

### Runtime Validation

```python
from bookalimo.config import DEFAULT_BASE_URL
import httpx

def validate_config(base_url: str, timeout: float, retries: int):
    """Validate configuration parameters."""
    # URL validation
    if not base_url.startswith(('http://', 'https://')):
        raise ValueError("base_url must be a valid HTTP(S) URL")

    # Timeout validation
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    # Retry validation
    if retries < 0:
        raise ValueError("retries must be non-negative")

    # Test connectivity
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{base_url.rstrip('/')}/health", timeout=5.0)
            if response.status_code != 200:
                print(f"Warning: API endpoint returned {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not validate endpoint: {e}")

# Usage
validate_config(DEFAULT_BASE_URL, 5.0, 2)
```

### Configuration Classes

```python
from dataclasses import dataclass
from typing import Optional
import httpx

@dataclass
class BookalimoConfig:
    """Configuration container for Bookalimo client."""
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 5.0
    retries: int = 2
    backoff: float = 0.3
    user_agent: Optional[str] = None

    def create_client(self, credentials):
        """Create client with this configuration."""
        from bookalimo import AsyncBookalimo
        return AsyncBookalimo(
            credentials=credentials,
            base_url=self.base_url,
            timeouts=httpx.Timeout(self.timeout),
            retries=self.retries,
            backoff=self.backoff,
            user_agent=self.user_agent
        )

# Usage
config = BookalimoConfig(
    base_url="https://staging.bookalimo.com/web/api",
    timeout=10.0,
    retries=5
)

client = config.create_client(credentials)
```
