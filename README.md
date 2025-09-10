# Bookalimo Python SDK

[![codecov](https://codecov.io/gh/asparagusbeef/bookalimo-python/branch/main/graph/badge.svg?token=H588J8Q1M8)](https://codecov.io/gh/asparagusbeef/bookalimo-python)
[![Docs](https://img.shields.io/github/deployments/asparagusbeef/bookalimo-python/github-pages?label=docs&logo=github)](https://asparagusbeef.github.io/bookalimo-python)
[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Python client library for the Book-A-Limo transportation booking API with async/sync support, type safety, and Google Places integration.

## Design philosophy: IDE-first DX

The library is **comprehensively typed** and **richly documented** via docstrings. Most users can rely on IDE hints, docstrings, and autocomplete without reading the docs.

## Features

- **Async & Sync Support** – `AsyncBookalimo` and `Bookalimo` clients
- **Type Safety** – Full Pydantic models with validation
- **Google Places Integration** – Location search and geocoding
- **Automatic Retry** – Built-in exponential backoff
- **Resource Management** – Context managers for proper cleanup

## Installation

```bash
pip install bookalimo

# With Google Places integration
pip install bookalimo[places]
```

## Quick Example

```python
import asyncio
from bookalimo import (
    AsyncBookalimo,
)
from bookalimo.transport.auth import (
    Credentials,
)
from bookalimo.schemas import (
    RateType,
    Location,
    LocationType,
    Address,
    City,
    Airport,
    PriceRequest,
    BookRequest,
)


async def book_ride():
    credentials = Credentials.create(
        "your_id",
        "your_password",
        is_customer=False,
    )

    pickup = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="Empire State Building",
            city=City(
                city_name="New York",
                country_code="US",
                state_code="NY",
            ),
        ),
    )
    dropoff = Location(
        type=LocationType.AIRPORT,
        airport=Airport(iata_code="JFK"),
    )

    async with AsyncBookalimo(credentials=credentials) as client:
        # Get pricing
        quote = await client.pricing.quote(
            PriceRequest(
                rate_type=RateType.P2P,
                date_time="12/25/2024 03:00 PM",
                pickup=pickup,
                dropoff=dropoff,
                passengers=2,
                luggage=2,
            )
        )

        # Book reservation
        booking = await client.reservations.book(
            BookRequest(
                token=quote.token,
                method="charge",
            )
        )
        return booking.reservation_id


confirmation = asyncio.run(book_ride())
```

## Sync Usage

```python
from bookalimo import (
    Bookalimo,
)

with Bookalimo(credentials=credentials) as client:
    quote = client.pricing.quote(PriceRequest(...))
    booking = client.reservations.book(
        BookRequest(
            token=quote.token,
            method="charge",
        )
    )
```

## Google Places Integration

```python
async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-google-places-key",
) as client:
    # Search locations
    results = await client.places.search("Hilton Miami Beach")

    # Resolve airports near landmarks
    airports = await client.places.resolve_airport(query="eiffel tower")
    top_airport = airports[0]  # Closest airport with confidence scoring

    # Use in booking flow
    quote = await client.pricing.quote(...)
```

## Error Handling

```python
from bookalimo.exceptions import (
    BookalimoHTTPError,
    BookalimoValidationError,
)

try:
    booking = await client.reservations.book(...)
except BookalimoValidationError as e:
    print(f"Invalid input: {e.message}")
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed")
```

## Environment

```bash
export GOOGLE_PLACES_API_KEY="your_google_places_key"
export BOOKALIMO_LOG_LEVEL="DEBUG"
```

## Documentation

**📖 Complete Documentation:** [https://asparagusbeef.github.io/bookalimo-python](https://asparagusbeef.github.io/bookalimo-python)

## Requirements

* Python 3.9+
* Book-A-Limo API credentials
* Dependencies: httpx, pydantic, pycountry, us, airportsdata, typing-extensions for Python 3.9-3.10
  - Optional: google-maps-places, google-api-core, numpy, rapidfuzz

## Support & Resources

* GitHub: [https://github.com/asparagusbeef/bookalimo-python](https://github.com/asparagusbeef/bookalimo-python)
* PyPI: [https://pypi.org/project/bookalimo/](https://pypi.org/project/bookalimo/)
* Issues: [https://github.com/asparagusbeef/bookalimo-python/issues](https://github.com/asparagusbeef/bookalimo-python/issues)
* Changelog: [CHANGELOG.md](./CHANGELOG.md)

## License

MIT License — see [LICENSE](LICENSE) for details.
