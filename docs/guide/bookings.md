# Making Bookings

Complete guide to booking transportation services through the Bookalimo SDK.

## Booking Workflow

Every booking follows the same three-step process:

1. **Get Pricing** - Request quotes for vehicle options
2. **Update Details** - Optionally modify booking details  
3. **Book Reservation** - Confirm and pay for the booking

## Step 1: Get Pricing

### Basic Pricing Request

```python
from bookalimo.schemas.booking import RateType, Location, LocationType, Address, City

# Define locations
pickup = Location(
    type=LocationType.ADDRESS,
    address=Address(
        place_name="Empire State Building",
        street_name="350 5th Ave",
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

# Get pricing
async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup,
        dropoff=dropoff,
        passengers=2,
        luggage=2
    )
    
    print(f"Session token: {quote.token}")
    print(f"Available vehicles: {len(quote.prices)}")
```

### Rate Types

**Point-to-Point (P2P)**
```python
quote = await client.pricing.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup_location,
    dropoff=dropoff_location,
    passengers=2,
    luggage=2
)
```

**Hourly Service**
```python
quote = await client.pricing.quote(
    rate_type=RateType.HOURLY,
    date_time="12/25/2024 09:00 AM",
    pickup=pickup_location,
    dropoff=pickup_location,  # Same location for hourly
    hours=4,  # Required for hourly bookings
    passengers=3,
    luggage=1
)
```

**Daily Service**
```python
quote = await client.pricing.quote(
    rate_type=RateType.DAILY,
    date_time="12/25/2024 08:00 AM", 
    pickup=hotel_location,
    dropoff=hotel_location,
    passengers=4,
    luggage=4
)
```

### Advanced Options

**With Stops**
```python
from bookalimo.schemas.booking import Stop

stops = [
    Stop(description="Grand Central Terminal", is_en_route=True),
    Stop(description="Times Square", is_en_route=False)
]

quote = await client.pricing.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup,
    dropoff=dropoff,
    passengers=2,
    luggage=2,
    stops=stops
)
```

**With Passenger Details**
```python
from bookalimo.schemas.booking import Passenger

passenger = Passenger(
    first_name="John",
    last_name="Doe", 
    email="john.doe@example.com",
    phone="+1234567890"
)

quote = await client.pricing.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup,
    dropoff=dropoff,
    passengers=2,
    luggage=2,
    passenger=passenger,
    customer_comment="VIP client - premium service preferred"
)
```

**Travel Agency Commission**
```python
from bookalimo.schemas.booking import Account

account = Account(
    id="TA12345",
    department="Corporate Travel",
    booker_first_name="Jane",
    booker_last_name="Smith",
    booker_email="jane@travelagency.com",
    booker_phone="+1234567890"
)

quote = await client.pricing.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup,
    dropoff=dropoff,
    passengers=2,
    luggage=2,
    account=account  # Required for commission
)
```

### Understanding Price Response

```python
quote = await client.pricing.quote(...)

for price in quote.prices:
    print(f"Vehicle: {price.car_class} - {price.car_description}")
    print(f"  Capacity: {price.max_passengers} passengers, {price.max_luggage} bags")
    print(f"  Base price: ${price.price}")
    print(f"  With meet & greet: ${price.price_default}")
    
    # Available meet & greet options
    for mg in price.meet_greets:
        print(f"    {mg.name}: ${mg.total_price} ({mg.instructions})")
```

## Step 2: Update Details (Optional)

Modify booking details and get updated pricing:

```python
# Update vehicle class and add special requests
details = await client.pricing.update_details(
    token=quote.token,
    car_class_code="LX",  # Upgrade to luxury
    customer_comment="Updated: Need child car seat",
    car_seats=1
)

print(f"Updated price: ${details.price}")
print("Price breakdown:")
for item in details.breakdown:
    prefix = "  " if not item.is_grand else "* "
    print(f"{prefix}{item.name}: ${item.value}")
```

### Common Updates

**Change Vehicle Class**
```python
details = await client.pricing.update_details(
    token=quote.token,
    car_class_code="SD"  # Standard sedan
)
```

**Add Special Requirements**
```python
details = await client.pricing.update_details(
    token=quote.token,
    pets=1,
    car_seats=2,
    boosters=1,
    customer_comment="Family with pets and children"
)
```

**Travel Agency Fee**
```python
details = await client.pricing.update_details(
    token=quote.token,
    ta_fee=25.00  # Additional agency fee
)
```

## Step 3: Book Reservation

### Credit Card Booking

```python
from bookalimo.schemas.booking import CreditCard, CardHolderType

credit_card = CreditCard(
    number="4111111111111111",
    expiration="12/25",
    cvv="123",
    card_holder="John Doe",
    zip="10001",
    holder_type=CardHolderType.PERSONAL
)

booking = await client.reservations.book(
    token=quote.token,
    credit_card=credit_card,
    promo="SAVE10"  # Optional promo code
)

print(f"✅ Booking confirmed: {booking.reservation_id}")
```

### Charge Account Booking

For agencies and corporate accounts:

```python
booking = await client.reservations.book(
    token=quote.token,
    method="charge"  # Bill to account on file
)

print(f"✅ Charged to account: {booking.reservation_id}")
```

## Complete Booking Examples

### Airport Transfer

```python
async def book_airport_transfer():
    """Book airport pickup service."""
    from bookalimo.schemas.booking import Airport
    
    # Airport pickup with flight details
    pickup = Location(
        type=LocationType.AIRPORT,
        airport=Airport(
            iata_code="JFK",
            flight_number="UA123",
            terminal="4",
            airline_iata_code="UA"
        )
    )
    
    # Hotel destination
    dropoff = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="Marriott Times Square",
            street_name="1535 Broadway",
            city=City(city_name="New York", country_code="US", state_code="NY")
        )
    )
    
    async with AsyncBookalimo(credentials=credentials) as client:
        # Get pricing
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 02:30 PM",  # Landing time + buffer
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=3,
            customer_comment="Flight arrival pickup"
        )
        
        # Select sedan with meet & greet
        details = await client.pricing.update_details(
            token=quote.token,
            car_class_code="SD"
        )
        
        # Book with credit card
        booking = await client.reservations.book(
            token=quote.token,
            credit_card=credit_card
        )
        
        return booking.reservation_id
```

### Hourly City Tour

```python
async def book_city_tour():
    """Book hourly service for sightseeing."""
    
    # Start at hotel
    pickup = Location(
        type=LocationType.ADDRESS,
        address=Address(
            place_name="The Plaza Hotel",
            street_name="768 5th Ave",
            city=City(city_name="New York", country_code="US", state_code="NY")
        )
    )
    
    # Tour stops
    stops = [
        Stop(description="Statue of Liberty", is_en_route=False),
        Stop(description="Brooklyn Bridge", is_en_route=True),
        Stop(description="Central Park", is_en_route=True),
        Stop(description="Times Square", is_en_route=False)
    ]
    
    async with AsyncBookalimo(credentials=credentials) as client:
        # 6-hour tour
        quote = await client.pricing.quote(
            rate_type=RateType.HOURLY,
            date_time="12/25/2024 09:00 AM",
            pickup=pickup,
            dropoff=pickup,  # Return to start
            hours=6,
            passengers=4,
            luggage=0,
            stops=stops,
            customer_comment="NYC sightseeing tour"
        )
        
        # Book luxury vehicle for tour
        details = await client.pricing.update_details(
            token=quote.token,
            car_class_code="LX"
        )
        
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"
        )
        
        return booking.reservation_id
```

### Corporate Booking with Account

```python
async def book_corporate_transfer():
    """Book corporate transfer with travel agency account."""
    from bookalimo.schemas.booking import Account, Passenger
    
    # Corporate account details
    account = Account(
        id="CORP12345",
        department="Executive Travel",
        booker_first_name="Sarah",
        booker_last_name="Johnson",
        booker_email="sarah.johnson@company.com",
        booker_phone="+12125551234"
    )
    
    # Executive traveler
    passenger = Passenger(
        first_name="Michael",
        last_name="Executive",
        email="michael.executive@company.com",
        phone="+12125559876"
    )
    
    async with AsyncBookalimo(credentials=credentials) as client:
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 06:00 AM",
            pickup=residence_location,
            dropoff=office_location,
            passengers=1,
            luggage=1,
            account=account,
            passenger=passenger,
            customer_comment="Daily executive commute"
        )
        
        # Select premium vehicle
        details = await client.pricing.update_details(
            token=quote.token,
            car_class_code="EX",  # Executive class
            ta_fee=15.00  # Agency service fee
        )
        
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"
        )
        
        return booking.reservation_id
```

## Error Handling in Bookings

### Common Booking Errors

```python
from bookalimo.exceptions import BookalimoHTTPError, BookalimoValidationError

async def robust_booking():
    try:
        quote = await client.pricing.quote(...)
        booking = await client.reservations.book(token=quote.token, ...)
        return booking.reservation_id
        
    except BookalimoValidationError as e:
        print(f"Invalid booking data: {e.message}")
        for error in e.errors():
            print(f"  {error['loc']}: {error['msg']}")
            
    except BookalimoHTTPError as e:
        if e.status_code == 400:
            print(f"Bad request: {e.payload}")
        elif e.status_code == 402:
            print("Payment failed - check credit card details")
        elif e.status_code == 409:
            print("Booking conflict - time slot may be unavailable") 
        else:
            print(f"HTTP {e.status_code}: {e}")
            
    return None
```

### Token Expiration Handling

```python
async def book_with_retry():
    """Handle expired session tokens."""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            # Try booking with current token
            booking = await client.reservations.book(
                token=current_token,
                credit_card=credit_card
            )
            return booking.reservation_id
            
        except BookalimoHTTPError as e:
            if e.status_code == 400 and "token" in str(e).lower():
                if attempt < max_retries - 1:
                    # Token expired, get new quote
                    print("Session expired, getting new quote...")
                    quote = await client.pricing.quote(...)
                    current_token = quote.token
                    continue
            raise
    
    raise RuntimeError("Booking failed after all retries")
```

## Best Practices

### Session Management

```python
class BookingSession:
    """Manage booking session state."""
    
    def __init__(self, client):
        self.client = client
        self.token = None
        self.current_price = None
        self.quote_params = None
    
    async def get_quote(self, **params):
        """Get initial pricing quote."""
        self.quote_params = params
        quote = await self.client.pricing.quote(**params)
        self.token = quote.token
        return quote
    
    async def update_details(self, **changes):
        """Update booking details."""
        if not self.token:
            raise ValueError("No active session - get quote first")
        
        details = await self.client.pricing.update_details(
            token=self.token, **changes
        )
        self.current_price = details.price
        return details
    
    async def book(self, **payment_info):
        """Complete the booking."""
        if not self.token:
            raise ValueError("No active session")
        
        return await self.client.reservations.book(
            token=self.token, **payment_info
        )
    
    async def refresh_quote(self):
        """Refresh expired session token."""
        if not self.quote_params:
            raise ValueError("No quote parameters stored")
        
        return await self.get_quote(**self.quote_params)

# Usage
session = BookingSession(client)
quote = await session.get_quote(...)
details = await session.update_details(car_class_code="LX")
booking = await session.book(credit_card=card)
```

### Price Comparison

```python
async def compare_vehicles(quote):
    """Compare available vehicle options."""
    vehicles = []
    
    for price in sorted(quote.prices, key=lambda p: p.price):
        vehicles.append({
            'class': price.car_class,
            'description': price.car_description,
            'price': price.price,
            'price_with_meetgreet': price.price_default,
            'capacity': f"{price.max_passengers}p/{price.max_luggage}bags",
            'savings': price.price_default - price.price
        })
    
    print("Vehicle Options (cheapest first):")
    for vehicle in vehicles:
        print(f"  {vehicle['class']}: ${vehicle['price']} ({vehicle['capacity']})")
        print(f"    {vehicle['description']}")
    
    return vehicles

# Usage  
quote = await client.pricing.quote(...)
options = await compare_vehicles(quote)
```

### Batch Bookings

```python
async def batch_book_transfers(transfer_requests):
    """Book multiple transfers efficiently."""
    results = []
    
    async with AsyncBookalimo(credentials=credentials) as client:
        for i, request in enumerate(transfer_requests):
            try:
                # Get quote
                quote = await client.pricing.quote(**request['booking_params'])
                
                # Book immediately to avoid token expiration
                booking = await client.reservations.book(
                    token=quote.token,
                    **request['payment_info']
                )
                
                results.append({
                    'index': i,
                    'confirmation': booking.reservation_id,
                    'success': True
                })
                
                # Rate limit between requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                results.append({
                    'index': i,
                    'error': str(e),
                    'success': False
                })
                
    return results

# Usage
transfers = [
    {
        'booking_params': {...},
        'payment_info': {'method': 'charge'}
    },
    # ... more transfers
]

results = await batch_book_transfers(transfers)
successful = [r for r in results if r['success']]
failed = [r for r in results if not r['success']]
```