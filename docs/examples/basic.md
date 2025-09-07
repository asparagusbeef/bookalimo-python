# Basic Usage Examples

Simple patterns for common booking scenarios.

## Point-to-Point Booking

```python
from bookalimo import Bookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import RateType, Location, LocationType, Address, City

credentials = Credentials.create("your_id", "your_password")

with Bookalimo(credentials=credentials) as client:
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
    
    # Get pricing and book
    quote = client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup,
        dropoff=dropoff,
        passengers=2,
        luggage=2
    )
    
    booking = client.reservations.book(
        token=quote.token,
        method="charge"
    )
    
    print(f"Booking confirmed: {booking.reservation_id}")
```

## Credit Card Payment

```python
from bookalimo.schemas.booking import CreditCard

credit_card = CreditCard(
    number="4111111111111111",
    expiration="12/25",
    cvv="123",
    card_holder="John Doe"
)

booking = client.reservations.book(
    token=quote.token,
    credit_card=credit_card
)
```

## List Reservations

```python
reservations = client.reservations.list(is_archive=False)

for reservation in reservations.reservations:
    print(f"{reservation.confirmation_number}: {reservation.pickup} → {reservation.dropoff}")
```