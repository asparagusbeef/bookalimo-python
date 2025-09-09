# Exceptions

SDK exception hierarchy for comprehensive error handling.

## Exception Types

### BookalimoError
Base exception for all SDK errors.

### BookalimoValidationError
Input validation errors with detailed field information:
```python
try:
    location = Location(type=LocationType.ADDRESS)  # Missing address
except BookalimoValidationError as e:
    print(f"Validation failed: {e.message}")
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

### BookalimoHTTPError
HTTP status errors with status code and payload:
```python
try:
    # Some Bookalimo operation
    pass
except BookalimoHTTPError as e:
    print(f"HTTP {e.status_code}: {e.payload}")
```

### BookalimoTimeout
Request timeout errors (specialized HTTP 408).

### BookalimoConnectionError
Network connectivity issues.

### BookalimoRequestError
General request errors.

## Exception Hierarchy

```
BookalimoError
├── BookalimoValidationError
├── BookalimoRequestError
├── BookalimoConnectionError
└── BookalimoHTTPError
    └── BookalimoTimeout
```
