# Google Places Examples

Location search and booking integration patterns.

## Basic Places Search

```python
from bookalimo import AsyncBookalimo

async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-key"
) as client:
    # Search for locations
    results = await client.places.search("JFK Airport")
    
    for place in results:
        print(f"{place.formatted_address} ({place.place_type})")
```

## Autocomplete Integration

```python
from bookalimo.schemas.places import AutocompletePlacesRequest

async def get_suggestions(query):
    request = AutocompletePlacesRequest(input=query)
    response = await client.places.autocomplete(request)
    
    suggestions = []
    for suggestion in response.suggestions:
        if suggestion.place_prediction:
            suggestions.append(suggestion.place_prediction.text.text)
    
    return suggestions
```

## Complete Booking with Places

```python
async def book_with_search():
    async with AsyncBookalimo(
        credentials=credentials,
        google_places_api_key="your-key"
    ) as client:
        # Search and select locations
        pickup_results = await client.places.search("JFK Airport")
        dropoff_results = await client.places.search("Empire State Building")
        
        # Convert to booking locations
        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                google_geocode=pickup_results[0].google_place.model_dump(),
                place_name=pickup_results[0].formatted_address
            )
        )
        
        dropoff = Location(
            type=LocationType.ADDRESS,
            address=Address(
                google_geocode=dropoff_results[0].google_place.model_dump(),
                place_name=dropoff_results[0].formatted_address
            )
        )
        
        # Complete booking
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