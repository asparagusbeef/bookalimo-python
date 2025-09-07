# Main Clients

Primary client classes providing high-level interfaces to the Book-A-Limo API with optional Google Places integration.

## AsyncBookalimo

::: bookalimo.client.AsyncBookalimo

Asynchronous client for the Book-A-Limo API with resource-style service access.

### Constructor

```python
client = AsyncBookalimo(
    credentials=credentials,
    base_url="https://www.bookalimo.com/web/api",
    timeouts=5.0,
    user_agent="my-app/1.0.0",
    transport=custom_transport,
    google_places_api_key="your-google-api-key"
)
```

**Parameters:**
- `credentials`: `Credentials` object for authentication (optional)
- `base_url`: API base URL (default from config)
- `timeouts`: Request timeout configuration
- `user_agent`: User agent string (default includes SDK version)
- `transport`: Custom `AsyncTransport` instance (optional)
- `google_places_api_key`: Google Places API key (optional)

### Service Properties

#### reservations

Access to reservation management operations:

```python
async with AsyncBookalimo(credentials=creds) as client:
    # List reservations
    reservations = await client.reservations.list()
    
    # Get specific reservation
    details = await client.reservations.get("ABC123")
    
    # Modify reservation
    edit_result = await client.reservations.edit("ABC123", passengers=3)
    
    # Book new reservation
    booking = await client.reservations.book(token=pricing_token, method="charge")
```

#### pricing

Access to pricing and quote operations:

```python
async with AsyncBookalimo(credentials=creds) as client:
    # Get pricing quote
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup_location,
        dropoff=dropoff_location,
        passengers=2,
        luggage=2
    )
    
    # Update details
    details = await client.pricing.update_details(
        token=quote.token,
        car_class_code="LX"
    )
```

#### places

Access to Google Places integration (optional):

```python
async with AsyncBookalimo(
    credentials=creds,
    google_places_api_key="your-key"
) as client:
    # Search for places
    results = await client.places.autocomplete("Empire State Building")
    
    # Get place details
    place = await client.places.get_place("places/ChIJ...")
    
    # Geocode address
    geocoded = await client.places.geocode("1600 Amphitheatre Parkway")
```

### Credential Management

The client handles credential precedence automatically:

**Priority Order:**
1. Transport credentials (if custom transport provided)
2. Constructor credentials
3. No credentials (unauthenticated)

**Warning System:**
- `DuplicateCredentialsWarning`: Both transport and constructor have credentials
- `MissingCredentialsWarning`: No credentials provided anywhere

```python
import warnings
from bookalimo.exceptions import DuplicateCredentialsWarning

# Suppress credential warnings if intentional
warnings.filterwarnings("ignore", category=DuplicateCredentialsWarning)

client = AsyncBookalimo(
    credentials=creds1,
    transport=AsyncTransport(credentials=creds2)
    # Uses creds2 from transport, warns about duplication
)
```

### Context Manager Usage

**Recommended Pattern:**
```python
async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(...)
    booking = await client.reservations.book(token=quote.token, ...)
    # Resources automatically cleaned up
```

**Manual Management:**
```python
client = AsyncBookalimo(credentials=credentials)
try:
    quote = await client.pricing.quote(...)
finally:
    await client.aclose()  # Important: manual cleanup
```

### Resource Management

#### aclose()

::: bookalimo.client.AsyncBookalimo.aclose

Properly closes all client resources:
- HTTP transport connections
- Google Places client (if used)

Always call when not using context manager:

```python
client = AsyncBookalimo(credentials=creds)
# ... use client ...
await client.aclose()
```

### Google Places Integration

The `places` property provides lazy initialization:

**Authentication Priority:**
1. Constructor `google_places_api_key`
2. `GOOGLE_PLACES_API_KEY` environment variable
3. Google Application Default Credentials (ADC)

**Exception Handling:**
```python
try:
    results = await client.places.autocomplete("query")
except ImportError:
    print("Google Places integration not installed")
    print("Install with: pip install bookalimo[places]")
```

## Bookalimo

::: bookalimo.client.Bookalimo

Synchronous client with identical interface using blocking I/O.

### Constructor

Same parameters as `AsyncBookalimo`:

```python
client = Bookalimo(
    credentials=credentials,
    base_url="https://www.bookalimo.com/web/api",
    google_places_api_key="your-key"
)
```

### Service Properties

Identical interfaces but with blocking operations:

```python
with Bookalimo(credentials=creds) as client:
    # Synchronous operations
    quote = client.pricing.quote(...)
    booking = client.reservations.book(token=quote.token, ...)
    places = client.places.autocomplete("query")
```

### Context Manager Usage

```python
# Recommended
with Bookalimo(credentials=credentials) as client:
    # Synchronous operations
    pass

# Manual cleanup
client = Bookalimo(credentials=credentials)
try:
    # Use client
    pass
finally:
    client.close()
```

## Client Selection Guide

### Choose AsyncBookalimo When:

- **High Concurrency**: Multiple simultaneous operations
- **I/O-Intensive**: Many API calls in sequence
- **Modern Architecture**: Already using asyncio
- **Web Applications**: Async web frameworks (FastAPI, aiohttp)
- **Long-Running Services**: Background processing, monitoring

**Example Use Cases:**
```python
# Concurrent pricing for multiple routes
async def get_multiple_quotes(routes):
    async with AsyncBookalimo(credentials=creds) as client:
        tasks = [
            client.pricing.quote(**route) 
            for route in routes
        ]
        return await asyncio.gather(*tasks)

# Real-time reservation monitoring
async def monitor_reservations():
    async with AsyncBookalimo(credentials=creds) as client:
        while True:
            reservations = await client.reservations.list()
            # Process reservations...
            await asyncio.sleep(60)
```

### Choose Bookalimo When:

- **Simple Scripts**: Command-line tools, batch processing
- **Legacy Code**: Synchronous codebases
- **Sequential Operations**: Step-by-step booking flows
- **Testing**: Simpler test scenarios
- **Learning**: Getting familiar with the API

**Example Use Cases:**
```python
# Simple booking script
def book_ride():
    with Bookalimo(credentials=creds) as client:
        quote = client.pricing.quote(...)
        booking = client.reservations.book(token=quote.token, ...)
        return booking.reservation_id

# Batch reservation processing
def process_bookings(booking_requests):
    with Bookalimo(credentials=creds) as client:
        results = []
        for request in booking_requests:
            quote = client.pricing.quote(**request)
            booking = client.reservations.book(token=quote.token, ...)
            results.append(booking.reservation_id)
        return results
```

## Configuration Examples

### Basic Configuration

```python
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials

# Create credentials
credentials = Credentials.create(
    user_id=os.getenv("BOOKALIMO_USER_ID"),
    password=os.getenv("BOOKALIMO_PASSWORD"),
    is_customer=False
)

# Basic client
async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(...)
```

### Advanced Configuration

```python
import httpx
from bookalimo import AsyncBookalimo
from bookalimo.transport import AsyncTransport

# Custom transport with specific timeouts
transport = AsyncTransport(
    base_url="https://api.bookalimo.com",
    timeouts=httpx.Timeout(
        connect=5.0,
        read=30.0,
        write=5.0,
        pool=2.0
    ),
    credentials=credentials,
    retries=5,
    backoff=1.0
)

# Client with custom transport
async with AsyncBookalimo(transport=transport) as client:
    # Uses custom transport configuration
    pass
```

### Production Configuration

```python
import os
import logging
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials

# Enable debug logging
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

# Production credentials from environment
credentials = Credentials.create(
    user_id=os.getenv("BOOKALIMO_USER_ID"),
    password=os.getenv("BOOKALIMO_PASSWORD"),
    is_customer=os.getenv("BOOKALIMO_IS_CUSTOMER", "false").lower() == "true"
)

# Production client with places integration
client = AsyncBookalimo(
    credentials=credentials,
    base_url=os.getenv("BOOKALIMO_API_URL", "https://www.bookalimo.com/web/api"),
    google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY"),
    user_agent=f"my-app/{__version__}"
)
```

### Testing Configuration

```python
import pytest
from unittest.mock import Mock
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials

@pytest.fixture
async def mock_client():
    # Mock transport for testing
    mock_transport = Mock()
    mock_transport.aclose = Mock()
    
    client = AsyncBookalimo(transport=mock_transport)
    yield client
    await client.aclose()

async def test_pricing(mock_client):
    # Mock the pricing response
    mock_client._transport.post.return_value = PriceResponse(...)
    
    quote = await mock_client.pricing.quote(...)
    assert quote.token is not None
```

## Error Handling Patterns

### Connection Errors

```python
from bookalimo.exceptions import BookalimoConnectionError, BookalimoTimeout

async def robust_client_usage():
    try:
        async with AsyncBookalimo(credentials=creds) as client:
            quote = await client.pricing.quote(...)
            return quote
            
    except BookalimoConnectionError:
        print("Unable to connect to Book-A-Limo API")
        # Implement fallback or retry logic
        
    except BookalimoTimeout:
        print("Request timed out")
        # Handle timeout scenario
```

### Authentication Errors

```python
from bookalimo.exceptions import BookalimoHTTPError

async def handle_auth_errors():
    try:
        async with AsyncBookalimo(credentials=invalid_creds) as client:
            quote = await client.pricing.quote(...)
            
    except BookalimoHTTPError as e:
        if e.status_code == 401:
            print("Authentication failed - check credentials")
        elif e.status_code == 403:
            print("Access forbidden - check account permissions")
        else:
            print(f"HTTP error: {e}")
```

### Service Integration

```python
class BookingService:
    def __init__(self, credentials, google_api_key=None):
        self.credentials = credentials
        self.google_api_key = google_api_key
    
    async def book_trip(self, pickup_address: str, dropoff_address: str):
        async with AsyncBookalimo(
            credentials=self.credentials,
            google_places_api_key=self.google_api_key
        ) as client:
            # Use Google Places to resolve addresses
            pickup_place = await client.places.autocomplete(pickup_address)
            dropoff_place = await client.places.autocomplete(dropoff_address)
            
            # Convert to booking locations
            pickup_location = self._convert_to_location(pickup_place)
            dropoff_location = self._convert_to_location(dropoff_place)
            
            # Get pricing and book
            quote = await client.pricing.quote(
                rate_type=RateType.P2P,
                pickup=pickup_location,
                dropoff=dropoff_location,
                # ... other parameters
            )
            
            booking = await client.reservations.book(
                token=quote.token,
                method="charge"
            )
            
            return booking.reservation_id
```