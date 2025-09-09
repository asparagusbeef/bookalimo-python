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
# Cancel reservation
await client.reservations.edit("ABC123", is_cancel=True)

# Modify details
await client.reservations.edit("ABC123", passengers=3, pickup_date="12/26/2024")
```

### book()

Book a reservation using session token from pricing:

```python
# Charge account
booking = await client.reservations.book(token=quote.token, method="charge")

# Credit card
booking = await client.reservations.book(token=quote.token, credit_card=CreditCard(...))
```
