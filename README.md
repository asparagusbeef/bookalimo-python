# Bookalimo Python SDK

[![codecov](https://codecov.io/gh/asparagusbeef/bookalimo-python/branch/main/graph/badge.svg?token=H588J8Q1M8)](https://codecov.io/gh/asparagusbeef/bookalimo-python)
[![Documentation Status](https://readthedocs.org/projects/bookalimo-python/badge/?version=latest)](https://bookalimo-python.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Python client library for the Book-A-Limo transportation booking API.

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

## Quick Example

```python
import asyncio
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import RateType

async def book_ride():
    credentials = Credentials.create("your_id", "your_password")
    
    async with AsyncBookalimo(credentials=credentials) as client:
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM",
            pickup=pickup_location,
            dropoff=dropoff_location,
            passengers=2,
            luggage=2
        )
        
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"
        )
        
        return booking.reservation_id

confirmation = asyncio.run(book_ride())
```

## Documentation

**📖 [Complete Documentation](https://asparagusbeef.github.io/bookalimo-python)**

- [Quick Start Guide](https://asparagusbeef.github.io/bookalimo-python/guide/quickstart/)
- [API Reference](https://asparagusbeef.github.io/bookalimo-python/api/)
- [Examples](https://asparagusbeef.github.io/bookalimo-python/examples/basic/)

## Requirements

- Python 3.9+
- Book-A-Limo API credentials

## License

MIT License - see [LICENSE](LICENSE) for details.
