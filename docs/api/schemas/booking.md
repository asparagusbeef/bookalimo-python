# Booking Models

Pydantic models for all Book-A-Limo booking operations including pricing, reservations, and location data.

## Enumerations

### RateType

::: bookalimo.schemas.booking.RateType

Rate types for different pricing models:

- `P2P = 0` - Point-to-Point transportation
- `HOURLY = 1` - Hourly rental 
- `DAILY = 2` - Daily rental
- `TOUR = 3` - Tour service
- `ROUND_TRIP = 4` - Round trip
- `RT_HALF = 5` - Round trip half-day

### LocationType

::: bookalimo.schemas.booking.LocationType

Types of locations supported:

- `ADDRESS = 0` - Street address or venue
- `AIRPORT = 1` - Airport with optional flight details
- `TRAIN_STATION = 2` - Train station
- `CRUISE = 3` - Cruise terminal

### MeetGreetType

::: bookalimo.schemas.booking.MeetGreetType

Meet & greet service options:

- `OTHER = 0` - Other/custom arrangement
- `FBO = 1` - Fixed Base Operator (private aviation)
- `BAGGAGE_CLAIM = 2` - Airport baggage claim area
- `CURB_SIDE = 3` - Curbside pickup
- `GATE = 4` - Airport gate
- `INTERNATIONAL = 5` - International arrivals
- `GREETER_SERVICE = 6` - Professional greeter service

### ReservationStatus

::: bookalimo.schemas.booking.ReservationStatus

Current status of reservations:

- `ACTIVE = None` - Active reservation
- `NO_SHOW = 0` - Customer no-show
- `CANCELED = 1` - Canceled reservation
- `LATE_CANCELED = 2` - Late cancellation

### CardHolderType

::: bookalimo.schemas.booking.CardHolderType

Credit card account types:

- `PERSONAL = 0` - Personal/individual account
- `BUSINESS = 1` - Business/corporate account  
- `UNKNOWN = 3` - Unknown account type

## Location Models

### City

::: bookalimo.schemas.booking.City

City location information with country and state validation.

**Validation Rules:**
- `country_code` must be valid ISO 3166-1 alpha-2
- For US locations, `state_code` and `state_name` are validated against US state data
- State code/name consistency is enforced for US locations

### Address

::: bookalimo.schemas.booking.Address

Street address or venue location.

**Validation Rules:**
- Either `place_name` or `street_name` must be provided
- Either `city` or `google_geocode` must be provided (but not both)
- `google_geocode` is preferred over `city` for accuracy

**Best Practices:**
```python
# Preferred: Use Google Geocoding API result
address = Address(
    google_geocode={...},  # Raw Google Geocoding response
    place_name="Empire State Building",
    building="350",
    street_name="5th Ave"
)

# Alternative: Manual city data
address = Address(
    city=City(city_name="New York", country_code="US", state_code="NY"),
    place_name="Empire State Building"
)
```

### Airport

::: bookalimo.schemas.booking.Airport

Airport location with optional flight information.

**Validation Rules:**
- `iata_code` must be valid 3-letter IATA airport code
- `country_code` validated against ISO 3166-1 alpha-2 if provided
- `state_code` validated against US states if provided

**Usage:**
```python
# Basic airport
airport = Airport(iata_code="JFK")

# With flight details
airport = Airport(
    iata_code="JFK",
    flight_number="UA123",
    terminal="4",
    arriving_from_city=City(city_name="London", country_code="GB")
)
```

### Location

::: bookalimo.schemas.booking.Location

Union type for address or airport locations.

**Validation Rules:**
- `address` required when `type=LocationType.ADDRESS`
- `airport` required when `type=LocationType.AIRPORT`

## Passenger and Account Models

### Passenger

::: bookalimo.schemas.booking.Passenger

Primary passenger information.

**Fields:**
- `first_name`: Required first name
- `last_name`: Required last name  
- `email`: Optional email address
- `phone`: Required phone number (E164 format recommended)

### Account

::: bookalimo.schemas.booking.Account

Travel agency or corporate account details.

**Usage:** Required for travel agents to receive commission.

### Reward

::: bookalimo.schemas.booking.Reward

Frequent flyer or loyalty program information.

### CreditCard

::: bookalimo.schemas.booking.CreditCard

Credit card payment information.

**Fields:**
- `number`: Card number
- `expiration`: MM/YY format
- `cvv`: Security code
- `card_holder`: Cardholder name
- `zip`: Optional billing ZIP code
- `holder_type`: Optional account type

## Pricing Models

### Price

::: bookalimo.schemas.booking.Price

Vehicle class pricing information.

**Key Fields:**
- `price`: Base price without meet & greet
- `price_default`: Price with default meet & greet service
- `meet_greets`: Available meet & greet options
- `max_passengers`/`max_luggage`: Vehicle capacity

### MeetGreet

::: bookalimo.schemas.booking.MeetGreet

Meet & greet service option with pricing.

### BreakdownItem

::: bookalimo.schemas.booking.BreakdownItem

Individual line item in price breakdown.

**Fields:**
- `name`: Description of charge
- `value`: Amount
- `is_grand`: Whether item represents a total/subtotal

## Request/Response Models

### PriceRequest

::: bookalimo.schemas.booking.PriceRequest

Request for getting vehicle pricing.

**Required Fields:**
- `rate_type`: Pricing model
- `date_time`: Pickup date/time in "MM/dd/yyyy hh:mm tt" format
- `pickup`: Pickup location
- `dropoff`: Dropoff location  
- `passengers`: Number of passengers
- `luggage`: Number of luggage pieces

**Optional Fields:**
- `hours`: Required for hourly bookings
- `stops`: Additional stops
- `account`: Travel agency account
- `car_class_code`: Specific vehicle class
- `customer_comment`: Special instructions

### PriceResponse

::: bookalimo.schemas.booking.PriceResponse

Pricing response with session token.

**Fields:**
- `token`: Session token for subsequent requests
- `prices`: List of available vehicle classes and pricing

### BookRequest

::: bookalimo.schemas.booking.BookRequest

Final booking request.

**Validation Rules:**
- Either `method="charge"` or `credit_card` must be provided

### BookResponse

::: bookalimo.schemas.booking.BookResponse

Successful booking confirmation.

**Fields:**
- `reservation_id`: Unique confirmation number

## Reservation Management

### Reservation

::: bookalimo.schemas.booking.Reservation

Basic reservation listing information.

### EditableReservationRequest

::: bookalimo.schemas.booking.EditableReservationRequest

Reservation modification request.

**Usage:**
```python
# Cancel reservation
edit_request = EditableReservationRequest(
    confirmation="ABC123",
    is_cancel_request=True
)

# Modify reservation
edit_request = EditableReservationRequest(
    confirmation="ABC123",
    passengers=3,  # Change passenger count
    pickup_date="12/25/2024"  # Change date
)
```

### GetReservationResponse

::: bookalimo.schemas.booking.GetReservationResponse

Detailed reservation information including editability status, pricing breakdown, and pending changes.

## Usage Examples

### Basic Pricing Request

```python
from bookalimo.schemas.booking import (
    PriceRequest, RateType, Location, LocationType, 
    Address, Airport, City
)

# Create locations
pickup_address = Address(
    place_name="Empire State Building",
    city=City(city_name="New York", country_code="US", state_code="NY")
)

dropoff_airport = Airport(iata_code="JFK")

# Build request
request = PriceRequest(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=Location(type=LocationType.ADDRESS, address=pickup_address),
    dropoff=Location(type=LocationType.AIRPORT, airport=dropoff_airport),
    passengers=2,
    luggage=2
)
```

### Complete Booking Flow

```python
# 1. Get pricing
price_request = PriceRequest(...)
price_response = await client.pricing.quote(...)

# 2. Update details if needed
details_response = await client.pricing.update_details(
    token=price_response.token,
    car_class_code="SD"
)

# 3. Book reservation
book_response = await client.reservations.book(
    token=price_response.token,
    credit_card=CreditCard(...)
)
```