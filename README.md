# Bookalimo Python SDK

[![codecov](https://codecov.io/gh/asparagusbeef/bookalimo-python/branch/main/graph/badge.svg?token=H588J8Q1M8)](https://codecov.io/gh/asparagusbeef/bookalimo-python)
[![Documentation Status](https://readthedocs.org/projects/bookalimo-python/badge/?version=latest)](https://bookalimo-python.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Python client library for the Book-A-Limo transportation booking API with async/sync support, type safety, and Google Places integration.

## Features

- **Async & Sync Support** - Choose the right client for your use case
- **Type Safety** - Full Pydantic models with validation
- **Google Places Integration** - Location search and geocoding
- **Automatic Retry** - Built-in exponential backoff for reliability
- **Comprehensive Error Handling** - Detailed exceptions with context

## Installation

```bash
pip install bookalimo

# With Google Places integration
pip install bookalimo[places]
```

## Core API

### Clients
- `AsyncBookalimo` - Async client for high-concurrency applications
- `Bookalimo` - Sync client for simple scripts and legacy code

### Services
- `client.pricing` - Get quotes and update booking details
- `client.reservations` - Book, list, modify, and cancel reservations
- `client.places` - Google Places search and geocoding (optional)

### Authentication
SHA256-based credential system with automatic password hashing:
```python
from bookalimo.transport.auth import Credentials

# Agency account
credentials = Credentials.create("AGENCY123", "password", is_customer=False)

# Customer account
credentials = Credentials.create("user@email.com", "password", is_customer=True)
```

### Booking Flow
1. **Get Pricing** - `client.pricing.quote()` returns session token + vehicle options
2. **Update Details** - `client.pricing.update_details()` modifies booking (optional)
3. **Book Reservation** - `client.reservations.book()` confirms with payment

## Quick Example

```python
import asyncio
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import RateType, Location, LocationType, Address, City

async def book_ride():
    credentials = Credentials.create("your_id", "your_password")

    # Define locations
    pickup = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="Empire State Building",
            city=City(city_name="New York", country_code="US", state_code="NY")
        )
    )

    dropoff = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="JFK Airport",
            city=City(city_name="New York", country_code="US", state_code="NY")
        )
    )

    async with AsyncBookalimo(credentials=credentials) as client:
        # 1. Get pricing
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=2
        )

        # 2. Book reservation
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"  # or credit_card=CreditCard(...)
        )

        return booking.reservation_id

confirmation = asyncio.run(book_ride())
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
        city=City(city_name="New York", country_code="US", state_code="NY")
    )
)

# Airport with flight details
airport_location = Location(
    type=LocationType.AIRPORT,
    airport=Airport(
        iata_code="JFK",
        flight_number="UA123",
        terminal="4"
    )
)
```

## Google Places Integration

```python
async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-google-places-key"
) as client:
    # Search locations
    results = await client.places.search("JFK Airport Terminal 4")

    # Convert to booking location
    location = Location(
        type=LocationType.ADDRESS,
        address=Address(
            google_geocode=results[0].google_place.model_dump(),
            place_name=results[0].formatted_address
        )
    )
```

## Reservation Management

```python
# List reservations
reservations = await client.reservations.list(is_archive=False)

# Get details
details = await client.reservations.get("ABC123")

# Modify reservation
edit_result = await client.reservations.edit(
    confirmation="ABC123",
    passengers=3,
    pickup_date="12/26/2024"
)

# Cancel reservation
cancel_result = await client.reservations.edit(
    confirmation="ABC123",
    is_cancel=True
)
```

## Error Handling

```python
from bookalimo.exceptions import BookalimoHTTPError, BookalimoValidationError

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
```

## Documentation

**📖 [Complete Documentation](https://asparagusbeef.github.io/bookalimo-python)**

- [Quick Start Guide](https://asparagusbeef.github.io/bookalimo-python/guide/quickstart/)
- [API Reference](https://asparagusbeef.github.io/bookalimo-python/api/)
- [Examples](https://asparagusbeef.github.io/bookalimo-python/examples/basic/)

## Environment Options

```bash
export GOOGLE_PLACES_API_KEY="your_google_places_key"
export BOOKALIMO_LOG_LEVEL="DEBUG"
```

## Requirements

- Python 3.9+
- Book-A-Limo API credentials
- Dependencies: httpx, pydantic, pycountry, us, airportsdata
- Optional: google-maps-places (for Places integration)

## License

MIT License - see [LICENSE](LICENSE) for details.
