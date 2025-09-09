# Pricing Service

Get quotes and update booking details with session token management.

## Methods

### quote()

Get pricing for a transportation request:

```python
quote = await client.pricing.quote(
    rate_type=RateType.P2P,
    date_time="12/25/2024 03:00 PM",
    pickup=pickup_location,
    dropoff=dropoff_location,
    passengers=2,
    luggage=2,
    # Optional parameters:
    hours=4,  # Required for RateType.HOURLY
    stops=[Stop(...)],
    account=Account(...),
    passenger=Passenger(...),
    car_class_code="SD",
    customer_comment="Special instructions",
)
```

Returns `PriceResponse` with:

- `token` - session token for subsequent requests
- `prices` - list of available vehicle classes

### update_details()

Update reservation details and get updated pricing:

```python
details = await client.pricing.update_details(
    token=quote.token,
    car_class_code="MVAN",  # Change vehicle class
    pickup=new_pickup_location,
    ta_fee=25.00,  # Travel agency fee
)
```

Returns `DetailsResponse` with:

- `price` - updated total price
- `breakdown` - itemized price breakdown
