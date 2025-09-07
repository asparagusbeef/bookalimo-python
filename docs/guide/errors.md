# Error Handling

Comprehensive error handling patterns for robust applications.

## Exception Hierarchy

```python
from bookalimo.exceptions import (
    BookalimoError,           # Base exception
    BookalimoValidationError, # Input validation errors
    BookalimoHTTPError,       # API/HTTP errors  
    BookalimoTimeout,         # Request timeouts
    BookalimoConnectionError  # Network connectivity
)
```

## Basic Error Handling

```python
try:
    async with AsyncBookalimo(credentials=credentials) as client:
        quote = await client.pricing.quote(...)
        booking = await client.reservations.book(token=quote.token, ...)
        
except BookalimoValidationError as e:
    print(f"Invalid input: {e.message}")
    
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed")
    elif e.status_code == 400:
        print(f"Bad request: {e.payload}")
    else:
        print(f"API error {e.status_code}: {e}")
        
except BookalimoTimeout:
    print("Request timed out - retry with backoff")
    
except BookalimoConnectionError:
    print("Network connectivity issue")
    
except BookalimoError as e:
    print(f"SDK error: {e}")
```

## Retry Pattern

```python
import asyncio

async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except (BookalimoTimeout, BookalimoConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Validation Error Details

```python
try:
    quote = await client.pricing.quote(invalid_params)
except BookalimoValidationError as e:
    print(f"Validation failed: {e.message}")
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

## Debug Logging

```python
import logging
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)
```