# Reservations Service

Manage the complete reservation lifecycle.

## Methods

### list()

List reservations for the authenticated user:

```python
# Active reservations
reservations = await client.reservations.list(is_archive=False)

# Historical reservations
archived = await client.reservations.list(is_archive=True)
```

### get()

Get detailed reservation information:

```python
details = await client.reservations.get("ABC123")
print(f"Status: {details.status}")
print(f"Can edit: {details.is_editable}")
```

### edit()

Modify or cancel a reservation:

```python
from bookalimo.schemas import EditReservationRequest

# Cancel reservation
await client.reservations.edit(
    EditReservationRequest(
        confirmation="ABC123", is_cancel_request=True
    )
)

# Modify details
await client.reservations.edit(
    EditReservationRequest(
        confirmation="ABC123",
        passengers=3,
        pickup_date="12/26/2024",
    )
)
```

### book()

Book a reservation using session token from pricing:

```python
from bookalimo.schemas import BookRequest, CreditCard

# Charge account
booking = await client.reservations.book(
    BookRequest(
        token=quote.token,
        method="charge",
    )
)

# Credit card
booking = await client.reservations.book(
    BookRequest(
        token=quote.token,
        credit_card=CreditCard(...),
    )
)
```
