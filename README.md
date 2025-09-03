# Book-A-Limo Python SDK

[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A modern, async Python wrapper for the Book-A-Limo API with full type support. Built on top of `httpx` and `pydantic`.

## Features

* **Asynchronous**
* **Fully Typed** for requests & responses
* **Input validation** including airports and addresses.
* **Clean, minimal interface** for each API operation
* **Custom exceptions & error handling**
* **Tests and examples**

## Requirements

* Python **3.9+** (`pyproject.toml` sets `requires-python = ">=3.9"`)
* An async event loop (examples use `asyncio`)
* Time strings use **`MM/dd/yyyy hh:mm tt`** (e.g., `09/05/2025 12:44 AM`)

## Installation

```bash
pip install bookalimo
```

## Quick Start

```python
import asyncio
from httpx import AsyncClient

from bookalimo import (
    BookALimo,
    create_credentials,
    create_airport_location,
    create_address_location,
)
from bookalimo.models import RateType  # enums/models come from bookalimo.models

async def main():
    # For Travel Agents (customers: pass is_customer=True)
    credentials = create_credentials("TA10007", "your_password")

    async with BookALimo(credentials) as client:
        # Build locations
        pickup = create_airport_location("JFK", "New York")
        dropoff = create_address_location("53 East 34th Street, Manhattan")

        prices = await client.get_prices(
            rate_type=RateType.P2P,
            date_time="09/05/2025 12:44 AM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=3,
        )

        print(f"Available cars: {len(prices.prices)}")
        for price in prices.prices:
            print(f"- {price.car_description}: ${price.price}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Authentication

```python
from bookalimo import create_credentials

# Travel Agents
ta_creds = create_credentials("TA10007", "password", is_customer=False)

# Customers
cust_creds = create_credentials("customer@email.com", "password", is_customer=True)
```

## Core Operations

```python
# List Reservations
reservations = await client.list_reservations(is_archive=False)

# Get Reservation Details
details = await client.get_reservation("5452773")
```

### Get Pricing

```python
from bookalimo.models import RateType

prices = await client.get_prices(
    rate_type=RateType.P2P,
    date_time="09/05/2025 12:44 AM",
    pickup=pickup,            # Location
    dropoff=dropoff,          # Location
    passengers=2,
    luggage=3,
    # Optional kwargs:
    # hours=2, stops=[...], account=..., passenger=..., rewards=[...],
    # car_class_code="SD", pets=0, car_seats=0, boosters=0, infants=0,
    # customer_comment="..."
)
```

### Book a Reservation

```python
from bookalimo import create_credit_card, create_passenger
from bookalimo.models import CardHolderType

# Optionally set details first (select car class, add passenger, etc.)
details = await client.set_details(
    token=prices.token,
    car_class_code="SD",
    passenger=create_passenger("John", "Smith", "+19173334455"),
)

# Book with credit card
card = create_credit_card(
    number="4111 1111 1111 1111",  # test PAN
    card_holder="John Smith",
    holder_type=CardHolderType.PERSONAL,
    expiration="01/28",
    cvv="123",
    zip_code="10016",
)

booking = await client.book(token=prices.token, credit_card=card)
print(f"Booked! Confirmation: {booking.reservation_id}")

# Or charge account
booking = await client.book(token=prices.token, method="charge")
```

## Location Builders

### Airport Locations

```python
from bookalimo import create_airport_location

pickup = create_airport_location(
    iata_code="JFK",
    city_name="New York",
    airline_code="UA",
    flight_number="UA1234",
    terminal="7",
)
```

### Address Locations

```python
from bookalimo import create_address_location

dropoff = create_address_location(
    address="53 East 34th Street, Manhattan",
    zip_code="10016",
)
```

### Stops

```python
from bookalimo import create_stop

stops = [
    create_stop("Brooklyn Bridge", is_en_route=False),
    create_stop("Empire State Building", is_en_route=True),
]
```

## Advanced

### Using Account Info (Travel Agents)

```python
from bookalimo.models import Account

account = Account(
    id="TA10007",
    department="Sales",
    booker_first_name="Jane",
    booker_last_name="Agent",
    booker_email="jane@agency.com",
    booker_phone="+19173334455",
)

prices = await client.get_prices(
    # ... required args
    account=account,
)
```

### Edit / Cancel a Reservation

```python
# Edit (e.g., add note or change passengers). Omitting fields leaves them unchanged.
edit_result = await client.edit_reservation(
    confirmation="5452773",
    is_cancel_request=False,
    passengers=3,
    other="Gate pickup",
)

# Cancel
cancel_result = await client.edit_reservation(
    confirmation="5452773",
    is_cancel_request=True,
)
```

## Error Handling

```python
from bookalimo.exceptions import BookALimoError

try:
    reservations = await client.list_reservations()
except BookALimoError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response Data: {e.response_data}")
```

## Development

```bash
# Clone & setup
git clone https://github.com/yourusername/bookalimo-python.git
cd bookalimo-python
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest
pytest --cov=bookalimo --cov-report=html

# Docs (MkDocs)
mkdocs serve
```

## Security Notes

* Never log raw passwords or credit card numbers.
* Store credentials securely (e.g., environment variables, secrets managers).

## License

This project is licensed under the MIT License — see [`LICENSE`](LICENSE).

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for release history.
