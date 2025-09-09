# Error Handling

The SDK provides specific exception types for different error scenarios.

## Exception Hierarchy

```
BookalimoError (base)
├── BookalimoValidationError (input validation)
├── BookalimoRequestError (general request issues)
├── BookalimoConnectionError (network connectivity)
└── BookalimoHTTPError (HTTP status errors)
    └── BookalimoTimeout (408 timeouts)
```

## Basic Error Handling

```python
from bookalimo.exceptions import (
    BookalimoValidationError,
    BookalimoHTTPError,
    BookalimoTimeout,
    BookalimoConnectionError,
    BookalimoError,
)

try:
    async with AsyncBookalimo(credentials=creds) as client:
        quote = await client.pricing.quote(...)
        booking = await client.reservations.book(token=quote.token, ...)

except BookalimoValidationError as e:
    print(f"Invalid input: {e.message}")
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")

except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed")
    elif e.status_code == 400:
        print(f"Bad request: {e.payload}")
    else:
        print(f"API error {e.status_code}: {e}")

except BookalimoTimeout:
    print("Request timed out")

except BookalimoConnectionError:
    print("Network connectivity issue")

except BookalimoError as e:
    print(f"SDK error: {e}")
```

## Common Scenarios

**Invalid Location Data**:
```python
try:
    location = Location(type=LocationType.ADDRESS)  # Missing address
except BookalimoValidationError as e:
    print(f"Location validation failed: {e.message}")
```

**Authentication Issues**:
```python
try:
    quote = await client.pricing.quote(...)
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Check your credentials")
```

**Session Token Expired**:
```python
try:
    booking = await client.reservations.book(token="expired_token", ...)
except BookalimoHTTPError as e:
    if e.status_code == 400 and "token" in str(e).lower():
        print("Session expired - get new quote")
