# Clients

Main entry points for the Bookalimo SDK.

## AsyncBookalimo

Async client for high-concurrency applications:

```python
from bookalimo import (
    AsyncBookalimo,
)
from bookalimo.transport.auth import (
    Credentials,
)

credentials = Credentials.create(
    "user_id",
    "password",
    is_customer=False,
)

async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="optional_google_key",
) as client:
    quote = await client.pricing.quote(PriceRequest(...))
    booking = await client.reservations.book(BookRequest(...))
```

## Bookalimo

Synchronous client for simple scripts:

```python
from bookalimo import (
    Bookalimo,
)

with Bookalimo(credentials=credentials) as client:
    quote = client.pricing.quote(PriceRequest(...))
    booking = client.reservations.book(BookRequest(...))
```

## Constructor Parameters

Both clients accept:

- `credentials` - authentication (from `Credentials.create()`)
- `base_url` - API endpoint (default: production)
- `timeouts` - request timeouts (default: 5.0s)
- `user_agent` - custom user agent
- `transport` - custom transport instance
- `google_places_api_key` - Google Places API key

## Services

All clients expose:

- `.pricing` - get quotes and update details
- `.reservations` - book, list, edit reservations
- `.places` - Google Places integration (requires `bookalimo[places]`)

## Credential Precedence

If both transport and constructor provide credentials:
1. Transport credentials are used
2. Constructor credentials are ignored
3. `DuplicateCredentialsWarning` is issued
