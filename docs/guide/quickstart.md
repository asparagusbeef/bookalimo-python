# Quickstart

Get a quote and book a reservation with the Bookalimo SDK.

## Installation

```bash
pip install bookalimo
```

## Authentication

Create credentials with your Book-A-Limo account:

```python
from bookalimo.transport.auth import (
    Credentials,
)

# Agency account
creds = Credentials.create(
    "AGENCY_ID",
    "password",
    is_customer=False,
)

# Customer account
creds = Credentials.create(
    "user@email.com",
    "password",
    is_customer=True,
)
```

## Basic Booking

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
)


async def main():
    creds = Credentials.create(
        "YOUR_ID",
        "YOUR_PASSWORD",
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

    async with AsyncBookalimo(credentials=creds) as client:
        # Get pricing
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=2,
        )

        # Book reservation
        booking = await client.reservations.book(
            token=quote.token,
            method="charge",
        )
        print(f"Reservation confirmed: {booking.reservation_id}")


asyncio.run(main())
```

## Sync Usage

For synchronous applications, replace `AsyncBookalimo` with `Bookalimo` and remove `await`:

```python
from bookalimo import (
    Bookalimo,
)

with Bookalimo(credentials=creds) as client:
    quote = client.pricing.quote(...)
    booking = client.reservations.book(
        token=quote.token,
        method="charge",
    )
```

## Next Steps

- [Bookings Guide](bookings.md) - complete booking workflows
- [Google Places](places.md) - location search integration
- [Error Handling](errors.md) - robust error management
- [API Reference](../api/index.md) - complete API documentation
