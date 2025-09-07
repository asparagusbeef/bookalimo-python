# Exceptions

Comprehensive exception hierarchy for handling errors in the Bookalimo SDK with specific error types and context preservation.

## Exception Hierarchy

```
BookalimoError (base)
├── BookalimoValidationError
├── BookalimoRequestError  
├── BookalimoConnectionError
└── BookalimoHTTPError
    └── BookalimoTimeout
```

## Base Exception

### BookalimoError

::: bookalimo.exceptions.BookalimoError

Base exception for all Bookalimo SDK errors.

**Usage:**
```python
from bookalimo.exceptions import BookalimoError

try:
    quote = await client.pricing.quote(...)
except BookalimoError as e:
    print(f"Bookalimo error: {e}")
    # Handle any SDK-related error
```

**Inheritance:**
All SDK exceptions inherit from `BookalimoError`, enabling catch-all error handling while preserving specific error information.

## Validation Errors

### BookalimoValidationError

::: bookalimo.exceptions.BookalimoValidationError

Validation errors for input data that wraps Pydantic ValidationError with enhanced context.

#### Constructor

```python
BookalimoValidationError(message: str, validation_error: ValidationError = None)
```

#### Properties and Methods

##### message
```python
@property
def message(self) -> str
```
Get the error message.

##### errors()
```python
def errors(**kwargs) -> list[ErrorDetails]
```
Get detailed validation errors if available. Compatible with Pydantic ValidationError.errors().

##### error_count()
```python
def error_count() -> int
```
Get the number of validation errors.

##### title  
```python
@property
def title(self) -> str
```
Get validation error title.

##### json()
```python  
def json(**kwargs) -> str
```
Get errors as JSON string, compatible with Pydantic ValidationError.json().

#### Class Methods

##### from_exception_data()
```python
@classmethod
def from_exception_data(
    cls,
    title: str,
    line_errors: list[InitErrorDetails],
    input_type: Literal["python", "json"] = "python", 
    hide_input: bool = False
) -> "BookalimoValidationError"
```
Create validation error from Pydantic error details.

##### from_validation_error()
```python
@classmethod
def from_validation_error(
    cls,
    validation_error: ValidationError,
    message: str = None
) -> "BookalimoValidationError"
```
Create BookalimoValidationError from existing ValidationError.

#### Usage Examples

**Basic Validation Error:**
```python
from bookalimo.exceptions import BookalimoValidationError
from pydantic import ValidationError

try:
    location = Location(type=LocationType.ADDRESS)  # Missing required address
except ValidationError as e:
    raise BookalimoValidationError.from_validation_error(e, "Invalid location data")
```

**Handling Validation Errors:**
```python
try:
    quote = await client.pricing.quote(...)
except BookalimoValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Error count: {e.error_count()}")
    
    for error in e.errors():
        print(f"Field {error['loc']}: {error['msg']}")
```

**JSON Error Output:**
```python
try:
    request = PriceRequest(...)
except BookalimoValidationError as e:
    error_json = e.json()
    # Returns Pydantic-compatible JSON error format
    print(error_json)
```

## Network and Request Errors

### BookalimoRequestError

::: bookalimo.exceptions.BookalimoRequestError

General request errors that don't fit other categories.

**Triggers:**
- Malformed requests
- Protocol errors
- Unexpected request issues

**Example:**
```python
try:
    booking = await client.reservations.book(token="invalid_token")
except BookalimoRequestError as e:
    print(f"Request error: {e}")
    # Handle request-specific issues
```

### BookalimoConnectionError

::: bookalimo.exceptions.BookalimoConnectionError

Network connectivity errors.

**Triggers:**
- DNS resolution failures
- Connection refused
- Network unreachable
- SSL/TLS handshake failures

**Example:**
```python
try:
    quote = await client.pricing.quote(...)
except BookalimoConnectionError as e:
    print("Unable to connect to Book-A-Limo API")
    # Implement retry logic or offline fallback
```

## HTTP Errors

### BookalimoHTTPError

::: bookalimo.exceptions.BookalimoHTTPError

HTTP-related errors (4xx, 5xx responses) with structured error information.

#### Constructor

```python
BookalimoHTTPError(
    message: str,
    *,
    status_code: int = None,
    payload: dict[str, Any] = None
)
```

#### Properties

##### message
```python
self.message: str
```
Human-readable error message.

##### status_code
```python
self.status_code: Optional[int]
```
HTTP status code if available.

##### payload
```python
self.payload: Optional[dict[str, Any]]
```
Structured error payload from API response.

#### String Representation

The `__str__` method provides intelligent error formatting:

```python
# With API error payload
str(error) → "HTTP 400: Invalid pickup location (status_code=400)"

# Without payload  
str(error) → "HTTP 400 (status_code=400)"

# No status code
str(error) → "Request failed"
```

#### Usage Examples

**Status Code Handling:**
```python
try:
    quote = await client.pricing.quote(...)
except BookalimoHTTPError as e:
    if e.status_code == 400:
        print(f"Bad request: {e.payload}")
    elif e.status_code == 401:
        print("Authentication failed")
    elif e.status_code >= 500:
        print("Server error - retry later")
    else:
        print(f"HTTP {e.status_code}: {e}")
```

**Payload Analysis:**
```python
try:
    booking = await client.reservations.book(...)
except BookalimoHTTPError as e:
    if e.payload and "error" in e.payload:
        api_error = e.payload["error"]
        print(f"API Error: {api_error}")
    
    # Log full payload for debugging
    import json
    print(json.dumps(e.payload, indent=2))
```

### BookalimoTimeout

::: bookalimo.exceptions.BookalimoTimeout

Request timeout errors, specialized subclass of `BookalimoHTTPError`.

#### Constructor

```python
BookalimoTimeout(message: str = "Request timeout", **kwargs)
```

#### Properties

- `status_code`: Always set to 408
- `message`: Timeout-specific message
- `payload`: Optional additional context

#### Usage

**Timeout Handling:**
```python
try:
    quote = await client.pricing.quote(...)
except BookalimoTimeout as e:
    print("Request timed out - API may be slow")
    # Implement retry with exponential backoff
    
except BookalimoHTTPError as e:
    # Handle other HTTP errors
    print(f"HTTP error: {e}")
```

**Timeout vs Connection Errors:**
```python
try:
    quote = await client.pricing.quote(...)
except BookalimoTimeout:
    # Server responded but too slowly
    print("Server is responding slowly")
except BookalimoConnectionError:
    # Cannot connect to server at all
    print("Server is unreachable")
```

## Warning Classes

### DuplicateCredentialsWarning

::: bookalimo.exceptions.DuplicateCredentialsWarning

Warning issued when credentials are provided in both client constructor and transport.

**Behavior:**
- Transport credentials take precedence
- Warning helps identify configuration issues

**Example:**
```python
import warnings
from bookalimo.exceptions import DuplicateCredentialsWarning

# Suppress if intentional
warnings.filterwarnings("ignore", category=DuplicateCredentialsWarning)

client = AsyncBookalimo(
    credentials=creds1,
    transport=AsyncTransport(credentials=creds2)
    # Uses creds2, warns about duplication
)
```

### MissingCredentialsWarning

::: bookalimo.exceptions.MissingCredentialsWarning

Warning issued when no credentials are provided anywhere.

**Impact:**
- API calls may fail with authentication errors
- Some endpoints work unauthenticated (rare)

**Example:**
```python
# Proceeding without credentials
client = AsyncBookalimo()  # Warning issued
# Most operations will fail with HTTP 401
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
from bookalimo.exceptions import (
    BookalimoError,
    BookalimoValidationError,
    BookalimoConnectionError, 
    BookalimoHTTPError,
    BookalimoTimeout
)

async def robust_quote_request(**params):
    try:
        async with AsyncBookalimo(credentials=creds) as client:
            return await client.pricing.quote(**params)
            
    except BookalimoValidationError as e:
        print(f"Invalid parameters: {e.message}")
        # Log validation details
        for error in e.errors():
            print(f"  {error['loc']}: {error['msg']}")
        return None
        
    except BookalimoTimeout:
        print("Request timed out - retrying with longer timeout")
        # Implement retry logic
        return await robust_quote_request(**params)
        
    except BookalimoConnectionError:
        print("Connection failed - check network connectivity")
        return None
        
    except BookalimoHTTPError as e:
        if e.status_code == 401:
            print("Authentication failed - check credentials")
        elif e.status_code == 429:
            print("Rate limited - waiting before retry")
            await asyncio.sleep(60)
            return await robust_quote_request(**params)
        else:
            print(f"HTTP error {e.status_code}: {e}")
        return None
        
    except BookalimoError as e:
        print(f"Unexpected SDK error: {e}")
        return None
```

### Retry Logic with Error Types

```python
import asyncio
from typing import Optional

async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0
):
    """Retry function with exponential backoff for appropriate errors."""
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
            
        except BookalimoTimeout:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Timeout on attempt {attempt + 1}, retrying in {delay}s")
            await asyncio.sleep(delay)
            
        except BookalimoConnectionError:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Connection error on attempt {attempt + 1}, retrying in {delay}s")
            await asyncio.sleep(delay)
            
        except BookalimoHTTPError as e:
            # Only retry on server errors
            if e.status_code and e.status_code >= 500:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt)
                print(f"Server error {e.status_code} on attempt {attempt + 1}, retrying in {delay}s")
                await asyncio.sleep(delay)
            else:
                # Don't retry client errors
                raise
                
        except BookalimoValidationError:
            # Never retry validation errors
            raise

# Usage
async def get_quote():
    async with AsyncBookalimo(credentials=creds) as client:
        return await client.pricing.quote(...)

quote = await retry_with_backoff(get_quote)
```

### Error Context Preservation

```python
import traceback
from datetime import datetime

class BookingError(Exception):
    """Application-specific error wrapping SDK errors."""
    
    def __init__(self, message: str, original_error: Exception):
        super().__init__(message)
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc()

async def safe_booking(**params):
    try:
        async with AsyncBookalimo(credentials=creds) as client:
            quote = await client.pricing.quote(**params)
            booking = await client.reservations.book(token=quote.token, ...)
            return booking.reservation_id
            
    except BookalimoValidationError as e:
        raise BookingError("Invalid booking parameters", e)
    except BookalimoHTTPError as e:
        raise BookingError(f"Booking API error: {e}", e)
    except BookalimoError as e:
        raise BookingError("Booking service unavailable", e)

# Usage with context preservation
try:
    reservation_id = await safe_booking(...)
except BookingError as e:
    print(f"Booking failed: {e}")
    print(f"Original error: {e.original_error}")
    print(f"Error type: {type(e.original_error).__name__}")
    # Log full context for debugging
    logger.error(f"Booking error at {e.timestamp}: {e.traceback}")
```

### Debugging Error Information

```python
import logging

# Enable debug logging to see full error context
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

try:
    quote = await client.pricing.quote(...)
except BookalimoError as e:
    # Full error details available in debug logs
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Additional context for HTTP errors
    if isinstance(e, BookalimoHTTPError):
        print(f"Status: {e.status_code}")
        print(f"Payload: {e.payload}")
    
    # Validation error details
    if isinstance(e, BookalimoValidationError):
        print(f"Validation errors: {e.error_count()}")
        print(e.json(indent=2))
```