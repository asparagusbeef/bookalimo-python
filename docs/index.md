# Bookalimo Python SDK

Python client library for the Book-A-Limo transportation booking API.

[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Async & Sync Support**: Choose the right client for your application
- **Type Safety**: Full Pydantic models with validation
- **Google Places Integration**: Location search and geocoding
- **Comprehensive Error Handling**: Detailed exceptions with context
- **Automatic Retry**: Built-in exponential backoff for resilience
- **Resource Management**: Context managers for proper cleanup

## Quick Start

### Installation

```bash
pip install bookalimo

# With Google Places integration
pip install bookalimo[places]
```

### Basic Usage

```python
import asyncio
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import RateType, Location, LocationType, Address, City

async def book_ride():
    # Create credentials
    credentials = Credentials.create(
        user_id="your_agency_id",
        password="your_password",
        is_customer=False  # False for agencies, True for customers
    )

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

    # Book transportation
    async with AsyncBookalimo(credentials=credentials) as client:
        # Get pricing
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=2
        )

        # Book reservation
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"  # or credit_card=CreditCard(...)
        )

        return booking.reservation_id

# Run the booking
confirmation = asyncio.run(book_ride())
print(f"Booking confirmed: {confirmation}")
```

### With Google Places

```python
async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-google-places-key"
) as client:
    # Search for locations
    pickup_results = await client.places.search("JFK Airport")
    dropoff_results = await client.places.search("Empire State Building")

    # Convert to booking locations and proceed with booking...
```

### Synchronous Usage

```python
from bookalimo import Bookalimo

with Bookalimo(credentials=credentials) as client:
    quote = client.pricing.quote(...)
    booking = client.reservations.book(token=quote.token, method="charge")
```

## Key Concepts

### Authentication

```python
from bookalimo.transport.auth import Credentials

# Agency/Corporate Account
agency_creds = Credentials.create(
    user_id="AGENCY123",
    password="password",
    is_customer=False
)

# Customer Account
customer_creds = Credentials.create(
    user_id="customer@email.com",
    password="password",
    is_customer=True
)
```

### Booking Flow

1. **Get Pricing**: `client.pricing.quote()` - Get vehicle options and session token
2. **Update Details**: `client.pricing.update_details()` - Optionally modify booking
3. **Book Reservation**: `client.reservations.book()` - Confirm and pay

### Error Handling

```python
from bookalimo.exceptions import BookalimoError, BookalimoHTTPError

try:
    booking = await client.reservations.book(...)
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed")
    else:
        print(f"API error: {e}")
except BookalimoError as e:
    print(f"SDK error: {e}")
```

## Documentation

### User Guides
- **[Quick Start](guide/quickstart.md)** - Get started in 5 minutes
- **[Authentication](guide/auth.md)** - Credential setup and security
- **[Making Bookings](guide/bookings.md)** - Complete booking workflows
- **[Google Places](guide/places.md)** - Location search integration
- **[Error Handling](guide/errors.md)** - Robust error management

### API Reference
- **[Overview](api/index.md)** - SDK architecture and components
- **[Clients](api/clients.md)** - Main client classes
- **[Schemas](api/schemas/booking.md)** - Data models and validation
- **[Services](api/services/pricing.md)** - Pricing and reservation operations
- **[Transport](api/transport/index.md)** - HTTP layer and authentication
- **[Exceptions](api/exceptions.md)** - Error handling reference

### Examples
- **[Basic Usage](examples/basic.md)** - Simple patterns
- **[Async Usage](examples/async.md)** - High-performance async patterns
- **[Google Places](examples/places.md)** - Location integration

## Requirements

- **Python 3.9+**
- **Dependencies**: httpx, pydantic, pycountry, us, airportsdata
- **Optional**: google-maps-places (for Places integration)

## Environment Setup

```bash
export BOOKALIMO_USER_ID="your_agency_id"
export BOOKALIMO_PASSWORD="your_password"
export BOOKALIMO_IS_CUSTOMER="false"
export GOOGLE_PLACES_API_KEY="your_google_places_key"
```

## Support & Resources

- **GitHub**: [asparagusbeef/bookalimo-python](https://github.com/asparagusbeef/bookalimo-python)
- **PyPI**: [bookalimo](https://pypi.org/project/bookalimo/)
- **Issues**: [GitHub Issues](https://github.com/asparagusbeef/bookalimo-python/issues)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)

## License

MIT License. See [LICENSE](https://github.com/asparagusbeef/bookalimo-python/blob/main/LICENSE) for details.
