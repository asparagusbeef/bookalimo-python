# Bookalimo Python SDK

[![PyPI version](https://badge.fury.io/py/bookalimo.svg)](https://badge.fury.io/py/bookalimo)
[![Python Support](https://img.shields.io/pypi/pyversions/bookalimo.svg)](https://pypi.org/project/bookalimo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Modern Python SDK for the Book-A-Limo API with clean, typed interfaces for booking transportation services.

## Quick Start

```bash
pip install bookalimo
# For Google Places integration:
pip install bookalimo[places]
```

**Async Usage:**
```python
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import RateType, Location, LocationType

# Create credentials
creds = Credentials.create("user_id", "password")

async with AsyncBookalimo(credentials=creds) as client:
    # Get pricing
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="09/10/2025 03:00 PM",
        pickup=Location(type=LocationType.AIRPORT, ...),
        dropoff=Location(type=LocationType.ADDRESS, ...),
        passengers=2,
        luggage=2,
    )

    # List reservations
    reservations = await client.reservations.list()
```

**Sync Usage:**
```python
from bookalimo import Bookalimo

with Bookalimo(credentials=creds) as client:
    quote = client.pricing.quote(...)
    reservations = client.reservations.list()
```

## Table of Contents

- [Bookalimo Python SDK](#bookalimo-python-sdk)
  - [Quick Start](#quick-start)
  - [Table of Contents](#table-of-contents)
  - [Development](#development)
  - [Security Notes](#security-notes)
  - [License](#license)
  - [Changelog](#changelog)

## Development

```bash
# Clone & setup
git clone https://github.com/asparagusbeef/bookalimo-python.git
cd bookalimo-python
pip install -e ".[dev,test]"
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
