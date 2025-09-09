# Google Places Integration

Use Google Places API for location search and address validation in booking workflows.

## Setup

```bash
pip install bookalimo[places]
```

```python
from bookalimo import AsyncBookalimo

async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-google-places-key"
) as client:
    # Google Places available via client.places
    results = await client.places.search("JFK Airport")
```

## Common Usage Patterns

### Location Search

```python
# Find airports
airports = await client.places.search("JFK airport")

# Find addresses
addresses = await client.places.search("Empire State Building")

# Find restaurants
restaurants = await client.places.search("restaurants near Times Square")
```

### Airport Resolution

For better airport matching with confidence scoring:

```python
# Resolve airports with advanced matching
airports = await client.places.resolve_airport(
    query="JFK New York international",
    max_distance_km=50,
    max_results=3,
    confidence_threshold=0.8
)

for airport in airports:
    print(f"{airport.name} ({airport.iata_code})")
    print(f"  Confidence: {airport.confidence:.2f}")

# Use the best match
if airports:
    best_airport = airports[0]
    airport_location = Location(
        type=LocationType.AIRPORT,
        airport=Airport(iata_code=best_airport.iata_code)
    )
```

### Address Autocomplete

```python
from bookalimo.schemas.places import AutocompletePlacesRequest

request = AutocompletePlacesRequest(
    input="Empire State",
    language_code="en-US"
)

response = await client.places.autocomplete(request)
for suggestion in response.suggestions:
    if suggestion.place_prediction:
        print(suggestion.place_prediction.text.text)
```

### Convert to Bookalimo Locations

```python
from bookalimo.schemas.booking import Location, LocationType, Address

def create_booking_location(place):
    """Convert Google Places result to Bookalimo location."""
    return Location(
        type=LocationType.ADDRESS,
        address=Address(
            google_geocode=place.google_place.model_dump(),
            place_name=place.formatted_address
        )
    )

# Usage
places = await client.places.search("Central Park")
location = create_booking_location(places[0])
```

## Complete Booking Example

```python
from bookalimo.schemas.booking import Location, LocationType, Address, Airport, RateType

async def book_with_places():
    async with AsyncBookalimo(
        credentials=credentials,
        google_places_api_key="your-key"
    ) as client:
        # Use airport resolution for better airport matching
        airports = await client.places.resolve_airport(
            query="JFK Airport Terminal 4",
            max_results=1
        )

        # Find destination
        dropoff_places = await client.places.search("Times Square")

        # Convert to booking locations
        if airports:
            # Use resolved airport
            pickup = Location(
                type=LocationType.AIRPORT,
                airport=Airport(iata_code=airports[0].iata_code)
            )
        else:
            # Fallback to regular search
            pickup_places = await client.places.search("JFK Airport")
            pickup = create_booking_location(pickup_places[0])

        dropoff = create_booking_location(dropoff_places[0])

        # Book normally
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
```
