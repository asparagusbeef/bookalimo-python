# Reservations Service

Service for managing reservations including listing, retrieving, editing, canceling, and booking operations.

## AsyncReservationsService

::: bookalimo.services.reservations.AsyncReservationsService

Asynchronous reservations service for complete reservation lifecycle management.

### Constructor

```python
service = AsyncReservationsService(transport)
```

- `transport`: `AsyncBaseTransport` instance for HTTP communication

### Methods

#### list()

::: bookalimo.services.reservations.AsyncReservationsService.list

List reservations for the authenticated user or agency.

**Parameters:**
- `is_archive`: Boolean to fetch archived/historical reservations (default: False)

**Returns:** `ListReservationsResponse` with:
- `success`: Operation success flag
- `reservations`: List of `Reservation` objects
- `error`: Error message if operation failed

**Example:**
```python
# Get active reservations
active = await reservations_service.list(is_archive=False)
print(f"Found {len(active.reservations)} active reservations")

# Get historical reservations  
archived = await reservations_service.list(is_archive=True)
for reservation in archived.reservations:
    print(f"{reservation.confirmation_number}: {reservation.pickup}")
```

#### get()

::: bookalimo.services.reservations.AsyncReservationsService.get

Get detailed information for a specific reservation.

**Parameters:**
- `confirmation`: Confirmation number string

**Returns:** `GetReservationResponse` with comprehensive reservation details:
- `reservation`: Editable reservation data
- `is_editable`: Whether reservation can be modified
- `status`: Current reservation status
- `is_cancellation_pending`: Pending cancellation flag
- `breakdown`: Detailed price breakdown
- `evoucher_url`: Electronic voucher link
- `receipt_url`: Receipt download link
- `pending_changes`: List of pending modifications

**Example:**
```python
details = await reservations_service.get("ABC123")

print(f"Status: {details.status}")
print(f"Can edit: {details.is_editable}")
print(f"Pickup: {details.pickup_description}")
print(f"Total: ${sum(item.value for item in details.breakdown if item.is_grand)}")

if details.evoucher_url:
    print(f"E-voucher: {details.evoucher_url}")
```

#### edit()

::: bookalimo.services.reservations.AsyncReservationsService.edit

Modify or cancel an existing reservation.

**Required Parameters:**
- `confirmation`: Confirmation number

**Optional Parameters:**
- `is_cancel`: Set True to cancel reservation
- `rate_type`: Change rate type
- `pickup_date`: New pickup date ("MM/dd/yyyy" format)
- `pickup_time`: New pickup time ("hh:mm tt" format)
- `stops`: Updated stop list
- `passengers`: Change passenger count
- `luggage`: Update luggage count
- `pets`: Change pet count
- `car_seats`: Update car seat requirements
- `boosters`: Change booster seat count
- `infants`: Update infant count
- `other`: Free-text description of other changes

**Returns:** `EditReservationResponse` with:
- `success`: Whether edit was successful

**Examples:**

```python
# Cancel reservation
cancel_result = await reservations_service.edit(
    confirmation="ABC123",
    is_cancel=True
)

# Modify reservation details
edit_result = await reservations_service.edit(
    confirmation="ABC123",
    passengers=4,
    pickup_date="12/26/2024",
    pickup_time="04:00 PM",
    other="Changed pickup time due to flight delay"
)

if edit_result.success:
    print("Reservation updated successfully")
```

#### book()

::: bookalimo.services.reservations.AsyncReservationsService.book

Book a reservation using session token from pricing service.

**Required Parameters:**
- `token`: Session token from `PricingService.quote()` or `update_details()`

**Payment Parameters (one required):**
- `method`: Set to "charge" for charge account billing
- `credit_card`: `CreditCard` object for card payment

**Optional Parameters:**
- `promo`: Promotional code

**Returns:** `BookResponse` with:
- `reservation_id`: Unique confirmation number for new reservation

**Examples:**

```python
# Charge account booking
booking = await reservations_service.book(
    token=pricing_token,
    method="charge"
)

# Credit card booking
booking = await reservations_service.book(
    token=pricing_token,
    credit_card=CreditCard(
        number="4111111111111111",
        expiration="12/25",
        cvv="123",
        card_holder="John Doe",
        zip="10001"
    ),
    promo="SAVE10"
)

print(f"Reservation confirmed: {booking.reservation_id}")
```

## ReservationsService

::: bookalimo.services.reservations.ReservationsService

Synchronous version with identical interface using `BaseTransport`.

### Methods

Same methods as async version but with blocking operations:

```python
# Sync version
reservations = reservations_service.list(is_archive=False)
details = reservations_service.get("ABC123")
edit_result = reservations_service.edit("ABC123", passengers=3)
booking = reservations_service.book(token=token, method="charge")
```

## Complete Booking Flow

### End-to-End Reservation

```python
from bookalimo.schemas.booking import CreditCard

# 1. Get pricing quote
quote = await pricing_service.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup_location,
    dropoff=dropoff_location,
    passengers=2,
    luggage=2
)

# 2. Optionally update details
details = await pricing_service.update_details(
    token=quote.token,
    car_class_code="LX"  # Upgrade to luxury
)

# 3. Book the reservation
booking = await reservations_service.book(
    token=quote.token,
    credit_card=CreditCard(
        number="4111111111111111",
        expiration="12/25", 
        cvv="123",
        card_holder="Jane Smith"
    )
)

print(f"Booked reservation: {booking.reservation_id}")

# 4. Get confirmation details
confirmation = await reservations_service.get(booking.reservation_id)
print(f"E-voucher: {confirmation.evoucher_url}")
```

## Reservation Management

### Status Monitoring

```python
from bookalimo.schemas.booking import ReservationStatus

# Check reservation status
details = await reservations_service.get("ABC123")

if details.status == ReservationStatus.ACTIVE:
    print("Reservation is confirmed and active")
elif details.status == ReservationStatus.CANCELED:
    print("Reservation has been canceled")
elif details.is_cancellation_pending:
    print("Cancellation is being processed")
```

### Modification Workflow

```python
async def modify_reservation(confirmation: str, **changes):
    # 1. Check if reservation is editable
    details = await reservations_service.get(confirmation)
    
    if not details.is_editable:
        raise ValueError("Reservation cannot be modified")
    
    # 2. Apply modifications
    result = await reservations_service.edit(
        confirmation=confirmation,
        **changes
    )
    
    if result.success:
        # 3. Get updated details
        updated = await reservations_service.get(confirmation)
        return updated
    else:
        raise ValueError("Modification failed")

# Usage
updated_reservation = await modify_reservation(
    "ABC123",
    passengers=3,
    pickup_time="05:00 PM"
)
```

### Bulk Operations

```python
async def get_all_reservations():
    """Get both active and archived reservations."""
    active = await reservations_service.list(is_archive=False)
    archived = await reservations_service.list(is_archive=True)
    
    all_reservations = active.reservations + archived.reservations
    return sorted(all_reservations, key=lambda r: r.local_date_time, reverse=True)

async def cancel_multiple_reservations(confirmation_numbers: list[str]):
    """Cancel multiple reservations."""
    results = []
    
    for confirmation in confirmation_numbers:
        try:
            result = await reservations_service.edit(
                confirmation=confirmation,
                is_cancel=True
            )
            results.append((confirmation, result.success))
        except Exception as e:
            results.append((confirmation, False, str(e)))
    
    return results
```

## Payment Methods

### Charge Account Billing

For travel agencies and corporate accounts with established credit:

```python
booking = await reservations_service.book(
    token=pricing_token,
    method="charge"  # Bills to account on file
)
```

### Credit Card Payment

For individual payments and new accounts:

```python
from bookalimo.schemas.booking import CreditCard, CardHolderType

credit_card = CreditCard(
    number="4111111111111111",
    expiration="12/26",
    cvv="123", 
    card_holder="John Doe",
    zip="10001",
    holder_type=CardHolderType.PERSONAL
)

booking = await reservations_service.book(
    token=pricing_token,
    credit_card=credit_card
)
```

## Error Handling

### Common Error Scenarios

**Invalid Confirmation Number:**
```python
try:
    details = await reservations_service.get("INVALID123")
except BookalimoHTTPError as e:
    if e.status_code == 404:
        print("Reservation not found")
```

**Non-Editable Reservation:**
```python
details = await reservations_service.get("ABC123")
if not details.is_editable:
    print(f"Cannot modify reservation: {details.status}")
    return

# Proceed with modifications...
```

**Payment Failures:**
```python
try:
    booking = await reservations_service.book(
        token=token,
        credit_card=invalid_card
    )
except BookalimoHTTPError as e:
    if "credit card" in str(e).lower():
        print("Payment failed - check card details")
    elif "token" in str(e).lower():
        print("Session expired - get new pricing quote")
```

**Booking Validation:**
```python
from bookalimo.exceptions import BookalimoRequestError

try:
    booking = await reservations_service.book(token=token)
    # Missing payment method
except BookalimoRequestError as e:
    print("Either method='charge' or credit_card must be provided")
```

## Best Practices

### Session Token Usage

```python
# Don't reuse expired tokens
async def safe_booking(pricing_service, reservations_service, **quote_params):
    try:
        # Get fresh quote
        quote = await pricing_service.quote(**quote_params)
        
        # Book immediately to avoid token expiration
        booking = await reservations_service.book(
            token=quote.token,
            method="charge"
        )
        return booking
        
    except BookalimoHTTPError as e:
        if "token" in str(e).lower():
            # Token expired, get new quote
            return await safe_booking(pricing_service, reservations_service, **quote_params)
        raise
```

### Reservation Monitoring

```python
async def monitor_reservation(confirmation: str, check_interval: int = 300):
    """Monitor reservation status changes."""
    import asyncio
    
    last_status = None
    
    while True:
        try:
            details = await reservations_service.get(confirmation)
            current_status = details.status
            
            if current_status != last_status:
                print(f"Status changed to: {current_status}")
                last_status = current_status
                
                if current_status in [ReservationStatus.CANCELED, ReservationStatus.NO_SHOW]:
                    break
            
            await asyncio.sleep(check_interval)
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(check_interval)
```

### Error Recovery

```python
async def robust_edit(confirmation: str, **changes):
    """Edit reservation with retry logic."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Check editability
            details = await reservations_service.get(confirmation)
            if not details.is_editable:
                raise ValueError("Reservation not editable")
            
            # Apply changes
            result = await reservations_service.edit(
                confirmation=confirmation,
                **changes
            )
            
            if result.success:
                return await reservations_service.get(confirmation)
            
        except BookalimoHTTPError as e:
            if attempt < max_retries - 1 and e.status_code >= 500:
                # Retry on server errors
                await asyncio.sleep(2 ** attempt)
                continue
            raise
        
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    
    raise RuntimeError("Edit failed after all retries")
```