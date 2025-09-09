# Bookalimo Python SDK

[![codecov](https://codecov.io/gh/asparagusbeef/bookalimo-python/branch/main/graph/badge.svg?token=H588J8Q1M8)](https://codecov.io/gh/asparagusbeef/bookalimo-python)
[![Docs](https://img.shields.io/github/deployments/asparagusbeef/bookalimo-python/github-pages?label=docs&logo=github)](https://asparagusbeef.github.io/bookalimo-python)
[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A modern, fully-typed Python SDK for the Book-A-Limo transportation booking API with async/sync support, type safety, Google Places integration, and ergonomic resource management via context managers.

## Important notes

- **Docs are in preview**: Many pages were AI-generated from the codebase and haven’t had a full manual review yet. In case of conflict, the code and docstrings are the source of truth. Please [report issues](https://github.com/asparagusbeef/bookalimo-python/issues) you find.
- **Terms & credentials**: Use of Book-A-Limo API and Google APIs are subject to their respective Terms of Service.

## Design philosophy: IDE-first DX

The library is **comprehensively typed** and **richly documented** via docstrings. Most users can rely on IDE hints, docstrings, and autocomplete without reading the docs.

## Features

- **Async & Sync Support** – Choose the right client for your use case
- **Type Safety** – Full Pydantic models with validation
- **Google Places Integration** – Autocomplete, search, details, and geocoding
- **Automatic Retry** – Built-in exponential backoff for reliability
- **Comprehensive Error Handling** – Detailed exceptions with context
- **Resource Management** – Context managers for proper cleanup

## Installation

```bash
pip install bookalimo

# With Google Places integration
pip install bookalimo[places]
```

## Core API

### Clients

* `AsyncBookalimo` – Async client for high-concurrency applications
* `Bookalimo` – Sync client for simple scripts and legacy code

### Services

* `client.pricing` – Get quotes and update booking details
* `client.reservations` – Book, list, modify, and cancel reservations
* `client.places` – Google Places search and geocoding (optional)

### Authentication

SHA256-based credential system with automatic password hashing:

```python
from bookalimo.transport.auth import Credentials

# Agency account
agency = Credentials.create("AGENCY123", "password", is_customer=False)

# Customer account
customer = Credentials.create("user@email.com", "password", is_customer=True)
```

### Booking Flow

1. **Get Pricing** – `client.pricing.quote()` returns session token + vehicle options
2. **Update Details** – `client.pricing.update_details()` finalize booking details
3. **Book Reservation** – `client.reservations.book()` confirms with payment

## Quick Examples

### Async example

```python
import asyncio
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import (
    RateType,
    Location,
    LocationType,
    Address,
    City,
    Airport,
)


async def book_ride():
    credentials = Credentials.create("your_id", "your_password", is_customer=False)

    pickup = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="Empire State Building",
            city=City(city_name="New York", country_code="US", state_code="NY"),
        ),
    )

    dropoff = Location(type=LocationType.AIRPORT, airport=Airport(iata_code="JFK"))

    async with AsyncBookalimo(credentials=credentials) as client:
        # 1) Get pricing
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=2,
        )

        # 2) Book reservation
        booking = await client.reservations.book(
            token=quote.token, method="charge"  # or credit_card=CreditCard(...)
        )
        return booking.reservation_id


confirmation = asyncio.run(book_ride())
```

### Sync example

```python
from bookalimo import Bookalimo
from bookalimo.transport.auth import Credentials

credentials = Credentials.create("your_id", "your_password", is_customer=False)

with Bookalimo(credentials=credentials) as client:
    quote = client.pricing.quote(...)
    booking = client.reservations.book(token=quote.token, method="charge")
```

## Rate Types & Options

```python
from bookalimo.schemas.booking import RateType

# Point-to-point transfer
quote = await client.pricing.quote(
    rate_type=RateType.P2P,
    pickup=pickup_location,
    dropoff=dropoff_location,
    # ...
)

# Hourly service (minimum 2 hours)
quote = await client.pricing.quote(
    rate_type=RateType.HOURLY,
    hours=4,
    pickup=pickup_location,
    dropoff=pickup_location,  # Same for hourly
    # ...
)

# Daily service
quote = await client.pricing.quote(
    rate_type=RateType.DAILY,
    pickup=hotel_location,
    dropoff=hotel_location,
    # ...
)
```

## Location Types

```python
from bookalimo.schemas.booking import Location, LocationType, Address, Airport, City

# Street address
address_location = Location(
    type=LocationType.ADDRESS,
    address=Address(
        place_name="Empire State Building",
        street_name="350 5th Ave",
        city=City(city_name="New York", country_code="US", state_code="NY"),
    ),
)

# Airport with flight details
airport_location = Location(
    type=LocationType.AIRPORT,
    airport=Airport(iata_code="JFK", flight_number="UA123", terminal="4"),
)
```

## Google Places Integration (Recommended flow)

```python
async with AsyncBookalimo(
    credentials=credentials, google_places_api_key="your-google-places-key"
) as client:
    # Search locations
    results = await client.places.search("Hilton Miami Beach")

    # OR
    # autocomplete = await client.places.autocomplete(input="Hilton Miami Beach")
    # top_result = autocomplete.suggestions[0].place_prediction.place
    # top_result_place_id = top_result.id

    # OR
    # resolve_airport = await client.places.resolve_airport(query="Hilton Miami Beach")
    # top_result = resolve_airport[0]
    # iata_code = top_result.iata_code

    # Get the top result
    top_result = results[0]

    # Get the top result geocode

    # By place_id
    top_result_place_id = top_result.google_place.id
    top_result_geocode = await client.places.geocode(place_id=top_result_place_id)

    # By lat-lng
    top_result_geocode = await client.places.geocode(
        lat=top_result.lat, lng=top_result.lng
    )

    # Convert to booking location
    location = Location(
        type=LocationType.ADDRESS,
        address=Address(
            google_geocode=top_result_geocode, place_name=top_result.formatted_address
        ),
    )
```

*(You can also search independent pickup/dropoff locations and feed them into the booking flow.)*

## Reservation Management

```python
# List reservations
reservations = await client.reservations.list(is_archive=False)

# Get details
details = await client.reservations.get("ABC123")

# Modify reservation
edit_result = await client.reservations.edit(
    confirmation="ABC123", passengers=3, pickup_date="12/26/2024"
)

# Cancel reservation
cancel_result = await client.reservations.edit(confirmation="ABC123", is_cancel=True)
```

## Error Handling

```python
from bookalimo.exceptions import (
    BookalimoError,  # base SDK error
    BookalimoHTTPError,  # HTTP/transport errors
    BookalimoValidationError,  # input/schema validation errors
)

try:
    booking = await client.reservations.book(...)
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
        print(f"API error: {e}")
except BookalimoError as e:
    print(f"SDK error: {e}")
```

## Documentation

**📖 Complete Documentation:** [https://asparagusbeef.github.io/bookalimo-python](https://asparagusbeef.github.io/bookalimo-python)

* Quick Start Guide: [https://asparagusbeef.github.io/bookalimo-python/guide/quickstart/](https://asparagusbeef.github.io/bookalimo-python/guide/quickstart/)
* API Reference: [https://asparagusbeef.github.io/bookalimo-python/api/](https://asparagusbeef.github.io/bookalimo-python/api/)
* Examples: [https://asparagusbeef.github.io/bookalimo-python/examples/basic/](https://asparagusbeef.github.io/bookalimo-python/examples/basic/)

## Environment

```bash
export GOOGLE_PLACES_API_KEY="your_google_places_key"
export BOOKALIMO_LOG_LEVEL="DEBUG"
```

## Requirements

* Python 3.9+
* Book-A-Limo API credentials
* Dependencies: httpx, pydantic, pycountry, us, airportsdata
  - Optional: google-maps-places, google-api-core, numpy, rapidfuzz

## Support & Resources

* GitHub: [https://github.com/asparagusbeef/bookalimo-python](https://github.com/asparagusbeef/bookalimo-python)
* PyPI: [https://pypi.org/project/bookalimo/](https://pypi.org/project/bookalimo/)
* Issues: [https://github.com/asparagusbeef/bookalimo-python/issues](https://github.com/asparagusbeef/bookalimo-python/issues)
* Changelog: [CHANGELOG.md](./CHANGELOG.md)

## License

MIT License — see [LICENSE](LICENSE) for details.
