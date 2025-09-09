# Booking Guide

Complete booking workflow from pricing to confirmation.

## Booking Flow

Every booking follows three steps:

1. **Get Pricing** - `client.pricing.quote()` returns session token + vehicle options
2. **Update Details** - `client.pricing.update_details()` (optional)
3. **Book Reservation** - `client.reservations.book()` confirms with payment

## Basic Example

```python
from bookalimo.schemas import (
    RateType,
    CreditCard,
)

async with AsyncBookalimo(credentials=creds) as client:
    # 1. Get pricing
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup_location,
        dropoff=dropoff_location,
        passengers=2,
        luggage=2,
    )

    # 2. Update details (optional)
    details = await client.pricing.update_details(
        token=quote.token,
        car_class_code="SD",  # Select sedan
        customer_comment="Flight arrival pickup",
    )

    # 3. Book with credit card
    booking = await client.reservations.book(
        token=quote.token,
        credit_card=CreditCard(
            number="4111111111111111",
            expiration="12/25",
            cvv="123",
            card_holder="John Doe",
        ),
    )

    print(f"Confirmed: {booking.reservation_id}")
```

## Rate Types

**Point-to-Point (`RateType.P2P`)**

- Fixed-rate transfers between two locations
- Most common for airport pickups

**Hourly (`RateType.HOURLY`)**

- Time-based service with minimum hours
- Requires `hours` parameter
- Same pickup/dropoff location

**Daily (`RateType.DAILY`)**

- Full-day service regardless of mileage

## Payment Methods

**Charge Account** (agencies/corporate):
```python
booking = await client.reservations.book(
    token=quote.token,
    method="charge",
)
```

**Credit Card**:
```python
booking = await client.reservations.book(
    token=quote.token,
    credit_card=card,
)
```

## Date/Time Format

Use `"MM/dd/yyyy hh:mm tt"` format:

- `"12/25/2024 03:00 PM"`
- `"01/15/2025 09:30 AM"`
