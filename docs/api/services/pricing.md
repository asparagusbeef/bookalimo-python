# Pricing Service

Service for retrieving vehicle pricing and updating reservation details with session token management.

## AsyncPricingService

::: bookalimo.services.pricing.AsyncPricingService

Asynchronous pricing service providing quote and detail update operations.

### Constructor

```python
service = AsyncPricingService(transport)
```

- `transport`: `AsyncBaseTransport` instance for HTTP communication

### Methods

#### quote()

::: bookalimo.services.pricing.AsyncPricingService.quote

Get pricing for a transportation request.

**Required Parameters:**
- `rate_type`: `RateType` enum (P2P, HOURLY, DAILY, etc.)
- `date_time`: Pickup date/time in "MM/dd/yyyy hh:mm tt" format  
- `pickup`: `Location` object for pickup point
- `dropoff`: `Location` object for destination
- `passengers`: Number of passengers (integer)
- `luggage`: Number of luggage pieces (integer)

**Optional Parameters:**
- `hours`: Required for `RateType.HOURLY` bookings
- `stops`: List of `Stop` objects for additional stops
- `account`: `Account` object for travel agency commission
- `passenger`: `Passenger` object with contact details
- `rewards`: List of `Reward` objects for loyalty programs
- `car_class_code`: Specific vehicle class (e.g., "SD" for sedan)
- `pets`: Number of pets
- `car_seats`: Number of child car seats needed
- `boosters`: Number of booster seats needed
- `infants`: Number of infants
- `customer_comment`: Special instructions or requests

**Returns:** `PriceResponse` with:
- `token`: Session token for subsequent requests
- `prices`: List of available vehicle classes and pricing

**Example:**
```python
from bookalimo.schemas.booking import RateType, Location, LocationType, Address, City

pickup = Location(
    type=LocationType.ADDRESS,
    address=Address(
        place_name="Empire State Building",
        city=City(city_name="New York", country_code="US", state_code="NY")
    )
)

quote = await pricing_service.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup,
    dropoff=dropoff_location,
    passengers=2,
    luggage=2,
    customer_comment="VIP client - premium service preferred"
)
```

#### update_details()

::: bookalimo.services.pricing.AsyncPricingService.update_details

Update reservation details and recalculate pricing.

**Required Parameters:**
- `token`: Session token from `quote()` response

**Optional Parameters:** Any field that can be modified:
- `car_class_code`: Change vehicle class
- `pickup`: Update pickup location
- `dropoff`: Update destination  
- `stops`: Modify stop list
- `account`: Update account information
- `passenger`: Change passenger details
- `rewards`: Modify loyalty programs
- `pets`: Update pet count
- `car_seats`: Change car seat requirements
- `boosters`: Update booster seat count
- `infants`: Change infant count
- `customer_comment`: Update special instructions
- `ta_fee`: Travel agency fee (for agencies)

**Returns:** `DetailsResponse` with:
- `price`: Updated total price
- `breakdown`: Itemized price breakdown

**Example:**
```python
# Update to premium vehicle class
details = await pricing_service.update_details(
    token=quote.token,
    car_class_code="LX",  # Luxury class
    customer_comment="Updated to luxury vehicle"
)

print(f"New price: ${details.price}")
for item in details.breakdown:
    print(f"{item.name}: ${item.value}")
```

## PricingService

::: bookalimo.services.pricing.PricingService

Synchronous version with identical interface using `BaseTransport`.

### Methods

Same interface as `AsyncPricingService` but with blocking operations:

```python
# Sync version
quote = pricing_service.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup,
    dropoff=dropoff,
    passengers=2,
    luggage=2
)

details = pricing_service.update_details(
    token=quote.token,
    car_class_code="SD"
)
```

## Session Management

The pricing service uses session tokens to maintain state:

1. **Initial Quote**: `quote()` returns a session token
2. **Detail Updates**: `update_details()` modifies the session
3. **Booking**: Token used in `ReservationsService.book()`

**Session Lifecycle:**
```python
# 1. Get initial pricing
quote = await pricing_service.quote(...)
token = quote.token

# 2. Optionally update details
details = await pricing_service.update_details(token=token, ...)

# 3. Book with final token
booking = await reservations_service.book(token=token, ...)
```

## Pricing Structure

### Price Response Format

```python
PriceResponse(
    token="session_abc123",
    prices=[
        Price(
            car_class="SD",
            car_description="Sedan - Up to 3 passengers",
            max_passengers=3,
            max_luggage=3,
            price=85.00,           # Base price without meet & greet
            price_default=95.00,   # Price with default meet & greet
            meet_greets=[          # Available meet & greet options
                MeetGreet(id=1, name="Curbside", base_price=10.00, ...),
                MeetGreet(id=2, name="Baggage Claim", base_price=15.00, ...)
            ]
        ),
        # Additional vehicle classes...
    ]
)
```

### Detail Response Format

```python
DetailsResponse(
    price=127.50,
    breakdown=[
        BreakdownItem(name="Base Fare", value=85.00, is_grand=False),
        BreakdownItem(name="Meet & Greet", value=15.00, is_grand=False),
        BreakdownItem(name="Gratuity", value=20.00, is_grand=False),
        BreakdownItem(name="Tax", value=7.50, is_grand=False),
        BreakdownItem(name="Total", value=127.50, is_grand=True)
    ]
)
```

## Rate Types and Pricing

### Point-to-Point (P2P)
- **Usage**: Airport transfers, city-to-city transport
- **Pricing**: Fixed rate based on distance and vehicle class
- **Required**: `pickup`, `dropoff` locations

### Hourly Rental
- **Usage**: Multiple stops, wait time, tours
- **Pricing**: Per-hour rate with minimum hours
- **Required**: `hours` parameter, typically 2-hour minimum

### Daily Rental
- **Usage**: Full-day service, business travel
- **Pricing**: Fixed daily rate regardless of mileage
- **Duration**: Typically 8-10 hour service day

### Tour Service
- **Usage**: Sightseeing, custom itineraries  
- **Pricing**: Custom pricing based on tour details
- **Flexibility**: Customizable stops and duration

## Error Handling

### Common Errors

**Validation Errors:**
```python
try:
    quote = await pricing_service.quote(
        rate_type=RateType.HOURLY,
        # Missing required 'hours' parameter
        ...
    )
except BookalimoValidationError as e:
    print(f"Validation error: {e.message}")
```

**Session Errors:**
```python
try:
    details = await pricing_service.update_details(
        token="invalid_token",
        car_class_code="SD"
    )
except BookalimoHTTPError as e:
    print(f"Session expired or invalid: {e}")
```

**Location Errors:**
```python
try:
    quote = await pricing_service.quote(
        pickup=invalid_location,  # Invalid IATA code, etc.
        ...
    )
except BookalimoError as e:
    print(f"Location error: {e}")
```

## Best Practices

### Quote Optimization

```python
# Include all known details in initial quote for accurate pricing
quote = await pricing_service.quote(
    rate_type=RateType.P2P,
    date_time=pickup_datetime,
    pickup=pickup_location,
    dropoff=dropoff_location,
    passengers=passenger_count,
    luggage=luggage_count,
    account=travel_agency_account,  # For commission calculation
    passenger=passenger_info,       # For better service
    car_class_code="LX"            # If class preference known
)
```

### Session Token Management

```python
# Store session token for multi-step booking process
class BookingSession:
    def __init__(self):
        self.token = None
        self.current_price = None
    
    async def get_quote(self, ...):
        quote = await pricing_service.quote(...)
        self.token = quote.token
        return quote
    
    async def update_vehicle(self, car_class_code: str):
        if not self.token:
            raise ValueError("No active session")
        
        details = await pricing_service.update_details(
            token=self.token,
            car_class_code=car_class_code
        )
        self.current_price = details.price
        return details
```

### Price Comparison

```python
# Compare vehicle classes efficiently
quote = await pricing_service.quote(...)

# Sort by price
vehicles = sorted(quote.prices, key=lambda p: p.price)
print(f"Cheapest: {vehicles[0].car_class} - ${vehicles[0].price}")
print(f"Most expensive: {vehicles[-1].car_class} - ${vehicles[-1].price}")

# Filter by capacity
suitable_vehicles = [
    p for p in quote.prices 
    if p.max_passengers >= required_passengers
]
```