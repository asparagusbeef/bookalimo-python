# Quick Start

Get up and running with the Bookalimo SDK in minutes.

## Installation

Install the Bookalimo SDK:

```bash
pip install bookalimo
```

For Google Places integration:

```bash
pip install bookalimo[places]
```

## Basic Setup

### 1. Get Credentials

Obtain your Book-A-Limo API credentials:

- **User ID**: Your agency or customer ID
- **Password**: Your account password
- **Account Type**: Agency (`is_customer=False`) or Customer (`is_customer=True`)

### 2. Create Client

```python
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials

# Create credentials
credentials = Credentials.create(
    user_id="your_agency_id",
    password="your_password",
    is_customer=False  # False for agencies, True for customers
)

# Create client
async with AsyncBookalimo(credentials=credentials) as client:
    # Ready to make API calls
    pass
```

## Your First Booking

Complete booking workflow from pricing to confirmation:

```python
import asyncio
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials
from bookalimo.schemas.booking import (
    RateType, Location, LocationType, Address, City, CreditCard
)

async def book_transportation():
    # Setup credentials
    credentials = Credentials.create(
        user_id="your_agency_id",
        password="your_password",
        is_customer=False
    )
    
    # Define locations
    pickup = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="Empire State Building",
            street_name="5th Ave",
            building="350",
            city=City(
                city_name="New York",
                country_code="US",
                state_code="NY"
            )
        )
    )
    
    dropoff = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="JFK Airport",
            city=City(
                city_name="New York", 
                country_code="US",
                state_code="NY"
            )
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
        
        print(f"Available vehicles: {len(quote.prices)}")
        for price in quote.prices:
            print(f"  {price.car_class}: ${price.price}")
        
        # 2. Book with credit card
        booking = await client.reservations.book(
            token=quote.token,
            credit_card=CreditCard(
                number="4111111111111111",  # Test card
                expiration="12/25",
                cvv="123",
                card_holder="John Doe"
            )
        )
        
        print(f"✅ Booking confirmed: {booking.reservation_id}")
        
        # 3. Get confirmation details
        details = await client.reservations.get(booking.reservation_id)
        print(f"Pickup: {details.pickup_description}")
        print(f"Dropoff: {details.dropoff_description}")

# Run the booking
asyncio.run(book_transportation())
```

## Synchronous Usage

For simpler applications, use the synchronous client:

```python
from bookalimo import Bookalimo

def book_transportation_sync():
    credentials = Credentials.create(
        user_id="your_agency_id",
        password="your_password"
    )
    
    with Bookalimo(credentials=credentials) as client:
        # Same API, blocking operations
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
            method="charge"  # For charge accounts
        )
        
        return booking.reservation_id

confirmation = book_transportation_sync()
print(f"Booking: {confirmation}")
```

## With Google Places

Find locations easily with integrated Google Places:

```python
async def book_with_places():
    credentials = Credentials.create(user_id="...", password="...")
    
    async with AsyncBookalimo(
        credentials=credentials,
        google_places_api_key="your_google_places_key"
    ) as client:
        # Find pickup location
        pickup_results = await client.places.search("JFK Airport Terminal 4")
        pickup_place = pickup_results[0]
        
        # Find destination  
        dropoff_results = await client.places.search("Times Square")
        dropoff_place = dropoff_results[0]
        
        # Convert to Bookalimo locations
        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                google_geocode=pickup_place.google_place.model_dump(),
                place_name=pickup_place.formatted_address
            )
        )
        
        dropoff = Location(
            type=LocationType.ADDRESS, 
            address=Address(
                google_geocode=dropoff_place.google_place.model_dump(),
                place_name=dropoff_place.formatted_address
            )
        )
        
        # Book as usual
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM", 
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=2
        )
        
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"
        )
        
        return booking.reservation_id

asyncio.run(book_with_places())
```

## Environment Configuration

Set up environment variables for production:

```bash
# .env file
BOOKALIMO_USER_ID=your_agency_id
BOOKALIMO_PASSWORD=your_password
BOOKALIMO_IS_CUSTOMER=false
GOOGLE_PLACES_API_KEY=your_google_places_key
```

```python
import os
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials

# Load from environment
credentials = Credentials.create(
    user_id=os.getenv("BOOKALIMO_USER_ID"),
    password=os.getenv("BOOKALIMO_PASSWORD"),
    is_customer=os.getenv("BOOKALIMO_IS_CUSTOMER", "false").lower() == "true"
)

# Client with environment-based configuration
async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY")
) as client:
    # Production-ready client
    pass
```

## Common Patterns

### List and Manage Reservations

```python
async with AsyncBookalimo(credentials=credentials) as client:
    # List active reservations
    reservations = await client.reservations.list(is_archive=False)
    
    for reservation in reservations.reservations:
        print(f"Reservation {reservation.confirmation_number}")
        print(f"  Date: {reservation.local_date_time}")
        print(f"  Route: {reservation.pickup} → {reservation.dropoff}")
        print(f"  Status: {reservation.status}")
    
    # Get detailed information
    if reservations.reservations:
        first_reservation = reservations.reservations[0]
        details = await client.reservations.get(first_reservation.confirmation_number)
        
        if details.is_editable:
            # Modify reservation
            edit_result = await client.reservations.edit(
                confirmation=first_reservation.confirmation_number,
                passengers=3  # Change passenger count
            )
            print(f"Edit successful: {edit_result.success}")
```

### Price Comparison

```python
async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup,
        dropoff=dropoff,
        passengers=2,
        luggage=2
    )
    
    # Sort by price
    sorted_prices = sorted(quote.prices, key=lambda p: p.price)
    
    print("Available vehicles (cheapest first):")
    for price in sorted_prices:
        print(f"  {price.car_class}: ${price.price}")
        print(f"    Capacity: {price.max_passengers} passengers, {price.max_luggage} bags")
        print(f"    Description: {price.car_description}")
```

### Error Handling

```python
from bookalimo.exceptions import BookalimoError, BookalimoHTTPError

async def robust_booking():
    try:
        async with AsyncBookalimo(credentials=credentials) as client:
            quote = await client.pricing.quote(...)
            booking = await client.reservations.book(token=quote.token, ...)
            return booking.reservation_id
            
    except BookalimoHTTPError as e:
        if e.status_code == 401:
            print("Authentication failed - check credentials")
        elif e.status_code == 400:
            print(f"Bad request: {e.payload}")
        else:
            print(f"HTTP error {e.status_code}: {e}")
            
    except BookalimoError as e:
        print(f"SDK error: {e}")
        
    return None
```

## Next Steps

- **[Authentication Guide](auth.md)**: Detailed credential setup and security
- **[Booking Guide](bookings.md)**: Advanced booking patterns and workflows
- **[Google Places Guide](places.md)**: Location search and integration
- **[Error Handling](errors.md)**: Comprehensive error management
- **[API Reference](../api/index.md)**: Complete API documentation

## Production Checklist

Before deploying to production:

- [ ] Store credentials securely (environment variables, key management)
- [ ] Implement proper error handling and logging
- [ ] Set up monitoring for API quotas and usage
- [ ] Test with production-like data and volumes
- [ ] Configure appropriate timeouts and retry logic
- [ ] Enable debug logging for troubleshooting