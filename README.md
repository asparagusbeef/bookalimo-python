# Book-A-Limo Python SDK

[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A modern, async Python wrapper for the Book-A-Limo API with full type support.

## Features

- **Async/await support** - Built on httpx for modern async Python
- **Full type hints** - Complete typing support with Pydantic models
- **Input validation** - Automatic validation of API inputs
- **Clean interface** - Simple, intuitive methods for all API operations
- **Error handling** - Comprehensive error handling with custom exceptions
- **Test coverage** - Extensive test suite with mocking

## Quick Start

### Installation

```bash
pip install bookalimo
```

### Basic Usage

```python
import asyncio
import httpx
from bookalimo import BookALimoWrapper, create_credentials

async def main():
    credentials = create_credentials("TA10007", "your_password")

    async with httpx.AsyncClient() as http_client:
        async with BookALimoWrapper(http_client, credentials) as client:
            # List reservations
            reservations = await client.list_reservations()
            print(f"Found {len(reservations.reservations)} reservations")

            # Get pricing
            from bookalimo import create_airport_location, RateType
            pickup = create_airport_location("JFK", "New York")
            dropoff = create_address_location("53 East 34th Street, Manhattan")

            prices = await client.get_prices(
                rate_type=RateType.P2P,
                date_time="09/05/2025 12:44 AM",
                pickup=pickup,
                dropoff=dropoff,
                passengers=2,
                luggage=3
            )

            print(f"Available cars: {len(prices.prices)}")
            for price in prices.prices:
                print(f"- {price.car_description}: ${price.price}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### Authentication

```python
from bookalimo import create_credentials

# For Travel Agents
credentials = create_credentials("TA10007", "password", is_customer=False)

# For Customers
credentials = create_credentials("customer@email.com", "password", is_customer=True)
```

### Core Operations

#### List Reservations
```python
reservations = await client.list_reservations(is_archive=False)
```

#### Get Reservation Details
```python
details = await client.get_reservation("5452773")
```

#### Get Pricing
```python
prices = await client.get_prices(
    rate_type=RateType.P2P,
    date_time="09/05/2025 12:44 AM",
    pickup=pickup_location,
    dropoff=dropoff_location,
    passengers=2,
    luggage=3
)
```

#### Book Reservation
```python
# Set details first
details = await client.set_details(
    token=prices.token,
    car_class_code="SD",
    passenger=create_passenger("John", "Smith", "+19173334455")
)

# Book with credit card
from bookalimo import create_credit_card, CardHolderType
card = create_credit_card(
    "4184 7284 3916 0355",
    "John Smith",
    CardHolderType.PERSONAL,
    "01/28",
    "123"
)

booking = await client.book(token=prices.token, credit_card=card)
print(f"Booked! Confirmation: {booking.reservation_id}")
```

## Location Types

### Airport Locations
```python
from bookalimo import create_airport_location

pickup = create_airport_location(
    iata_code="JFK",
    city_name="New York",
    airline_code="UA",
    flight_number="UA1234",
    terminal="7"
)
```

### Address Locations
```python
from bookalimo import create_address_location

dropoff = create_address_location(
    address="53 East 34th Street",
    district="Manhattan",
    zip_code="10016"
)
```

## Error Handling

```python
from bookalimo import BookALimoError

try:
    reservations = await client.list_reservations()
except BookALimoError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response Data: {e.response_data}")
```

## Advanced Usage

### Using with Account Information (Travel Agents)
```python
from bookalimo import Account

account = Account(
    id="TA10007",
    department="Sales",
    booker_first_name="Jane",
    booker_last_name="Agent",
    booker_email="jane@agency.com",
    booker_phone="+19173334455"
)

prices = await client.get_prices(
    # ... other params
    account=account
)
```

### Adding Stops
```python
from bookalimo import create_stop

stops = [
    create_stop("Brooklyn Bridge", is_en_route=False),
    create_stop("Empire State Building", is_en_route=True)
]

prices = await client.get_prices(
    # ... other params
    stops=stops
)
```

## Development

### Setup
```bash
git clone https://github.com/yourusername/bookalimo-python.git
cd bookalimo-python
pip install -e ".[dev]"
pre-commit install
```

### Testing
```bash
pytest
pytest --cov=bookalimo --cov-report=html
```

### Documentation
```bash
mkdocs serve
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes.
```

**Create `LICENSE`:**
```
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
