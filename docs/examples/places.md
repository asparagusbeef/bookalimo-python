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

## Airport Resolution

```python
# Advanced airport resolution with confidence scoring
async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-key"
) as client:
    # Resolve airports by text query
    airports = await client.places.resolve_airport(
        query="kennedy", # Top result will be JFK
        max_distance_km=50,
        max_results=3,
        confidence_threshold=0.8
    )

    print("Airport candidates:")
    for airport in airports:
        print(f"  {airport.name} ({airport.iata_code})")
        print(f"    City: {airport.city}")
            print(f"    Confidence: {airport.confidence:.2f}")

    # Use best match for booking
    if airports:
        best_airport = airports[0]
        airport_location = Location(
            type=LocationType.AIRPORT,
            airport=Airport(iata_code=best_airport.iata_code)
        )
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
from bookalimo.schemas.booking import Location, LocationType, Address, Airport, RateType

async def book_with_search():
    async with AsyncBookalimo(
        credentials=credentials,
        google_places_api_key="your-key"
    ) as client:
        # If you don't know IATA code, use airport resolution
        airports = await client.places.resolve_airport(
            query="John Kennedy",
            max_results=1
        )

        # Search for destination
        dropoff_results = await client.places.search("Empire State Building")

        # Convert to booking locations
        if airports:
            # Use resolved airport
            pickup = Location(
                type=LocationType.AIRPORT,
                airport=Airport(iata_code=airports[0].iata_code)
            )
        else:
            # Fallback to booking with address
            pickup_results = await client.places.search("John Kennedy")

            geocode = await client.places.geocode(pickup_results[0].google_place.id)
            pickup = Location(
                type=LocationType.ADDRESS,
                address=Address(
                    google_geocode=geocode,
                    place_name=pickup_results[0].formatted_address
                )
            )

        geocode = await client.places.geocode(dropoff_results[0].google_place.id)
        dropoff = Location(
            type=LocationType.ADDRESS,
            address=Address(
                google_geocode=geocode,
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
