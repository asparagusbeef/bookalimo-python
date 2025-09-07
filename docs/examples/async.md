# Async Usage Examples

High-performance async patterns for concurrent operations.

## Async Booking

```python
import asyncio
from bookalimo import AsyncBookalimo

async def book_ride():
    credentials = Credentials.create("your_id", "your_password")
    
    async with AsyncBookalimo(credentials=credentials) as client:
        quote = await client.pricing.quote(
            rate_type=RateType.P2P,
            date_time="12/25/2024 03:00 PM",
            pickup=pickup_location,
            dropoff=dropoff_location,
            passengers=2,
            luggage=2
        )
        
        booking = await client.reservations.book(
            token=quote.token,
            method="charge"
        )
        
        return booking.reservation_id

# Run async function
confirmation = asyncio.run(book_ride())
```

## Concurrent Bookings

```python
async def book_multiple_rides(booking_requests):
    async with AsyncBookalimo(credentials=credentials) as client:
        tasks = []
        
        for request in booking_requests:
            task = asyncio.create_task(book_single_ride(client, request))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def book_single_ride(client, request):
    quote = await client.pricing.quote(**request)
    booking = await client.reservations.book(token=quote.token, method="charge")
    return booking.reservation_id
```

## Error Handling with Async

```python
from bookalimo.exceptions import BookalimoError

async def robust_booking():
    try:
        async with AsyncBookalimo(credentials=credentials) as client:
            quote = await client.pricing.quote(...)
            booking = await client.reservations.book(token=quote.token, ...)
            return booking.reservation_id
    except BookalimoError as e:
        print(f"Booking failed: {e}")
        return None
```