# API Reference

Complete reference documentation for the Bookalimo Python SDK.

## Overview

The Bookalimo SDK provides a clean, typed interface to the Book-A-Limo transportation booking API. The SDK is organized into several key components:

- **Clients**: High-level interfaces for API access
- **Schemas**: Data models for requests and responses
- **Services**: Specialized API operations (pricing, reservations)
- **Transport**: HTTP communication layer
- **Integrations**: External service integrations (Google Places)
- **Exceptions**: Error handling and types

## Core Components

### [Main Clients](clients.md)
Primary SDK entry points with resource-style API access.

- `AsyncBookalimo` - Asynchronous client for high-concurrency applications
- `Bookalimo` - Synchronous client for simple use cases
- Service properties: `pricing`, `reservations`, `places`

### [Configuration](config.md)
Default settings and configuration options.

- API endpoints and timeouts
- Retry and backoff settings
- User agent and request configuration

### [Exceptions](exceptions.md)
Comprehensive error handling with context preservation.

- `BookalimoError` - Base exception class
- `BookalimoValidationError` - Input validation errors
- `BookalimoHTTPError` - HTTP status and API errors
- `BookalimoTimeout` - Request timeout handling

## Data Models

### [Base Models](schemas/base.md)
Foundation models providing automatic field conversion and serialization.

- `ApiModel` - Base class with camelCase/snake_case conversion
- Enum handling and unknown field management

### [Booking Models](schemas/booking.md)
Complete data models for transportation booking operations.

**Core Models:**
- `Location`, `Address`, `Airport` - Geographic locations
- `PriceRequest`, `PriceResponse` - Pricing operations
- `BookRequest`, `BookResponse` - Reservation booking
- `Reservation` - Reservation management

**Enumerations:**
- `RateType` - Pricing models (P2P, hourly, daily, tour)
- `LocationType` - Location categories
- `ReservationStatus` - Booking status tracking

### [Places Models](schemas/places.md)
Google Places API integration models for location services.

**Search and Results:**
- `AutocompletePlacesRequest`, `AutocompletePlacesResponse`
- `Place` - Structured place information
- `PlacePrediction` - Search suggestions

**Geographic Types:**
- `LatLng`, `Viewport` - Coordinate systems
- `LocationBias`, `LocationRestriction` - Search constraints

## Services

### [Pricing Service](services/pricing.md)
Vehicle pricing and quote management.

**Key Operations:**
- `quote()` - Get pricing for transportation requests
- `update_details()` - Modify reservation details and pricing

**Session Management:**
- Token-based pricing sessions
- Detail updates and final booking

### [Reservations Service](services/reservations.md)
Complete reservation lifecycle management.

**Key Operations:**
- `list()` - List user reservations
- `get()` - Retrieve detailed reservation information
- `edit()` - Modify or cancel reservations
- `book()` - Create new reservations

**Payment Methods:**
- Credit card processing
- Charge account billing

## Transport Layer

### [Transport Overview](transport/index.md)
HTTP communication foundation with retry logic and error handling.

- Base interfaces and data preparation
- Automatic retry with exponential backoff
- Comprehensive error mapping and logging

### [HTTP Clients](transport/http.md)
Concrete transport implementations using httpx.

- `AsyncTransport` - Asynchronous HTTP operations
- `SyncTransport` - Synchronous HTTP operations
- Client lifecycle management and configuration

### [Authentication](transport/auth.md)
Credential management and API authentication.

- `Credentials` model with automatic password hashing
- SHA256-based authentication algorithm
- Credential injection and security considerations

## Integrations

### [Google Places](integrations/places.md)
Location search and geocoding services.

**Core Features:**
- Place autocomplete and search
- Address validation and geocoding
- Seamless integration with booking workflows

**Client Classes:**
- `AsyncGooglePlaces` - Asynchronous operations
- `GooglePlaces` - Synchronous operations

## Quick Navigation

### Getting Started
- [Quick Start Guide](../guide/quickstart.md)
- [Authentication Setup](../guide/auth.md)
- [Making Your First Booking](../guide/bookings.md)

### Common Tasks
- **Pricing**: Use `client.pricing.quote()` for vehicle pricing
- **Booking**: Use `client.reservations.book()` to create reservations
- **Location Search**: Use `client.places.search()` for place lookup
- **Reservation Management**: Use `client.reservations` for booking operations

### Error Handling
- All SDK operations can raise `BookalimoError` or its subclasses
- Use specific exception types for targeted error handling
- HTTP errors include status codes and response payloads

### Best Practices
- Always use context managers (`async with` / `with`) for resource management
- Enable debug logging for troubleshooting: `logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)`
- Use async clients for high-concurrency applications
- Implement retry logic for transient network failures

## Code Examples

### Basic Booking Flow
```python
from bookalimo import AsyncBookalimo
from bookalimo.schemas.booking import RateType

async with AsyncBookalimo(credentials=credentials) as client:
    # Get pricing
    quote = await client.pricing.quote(
        rate_type=RateType.P2P,
        date_time="12/25/2024 03:00 PM",
        pickup=pickup_location,
        dropoff=dropoff_location,
        passengers=2,
        luggage=2
    )
    
    # Book reservation
    booking = await client.reservations.book(
        token=quote.token,
        method="charge"
    )
    
    print(f"Reservation confirmed: {booking.reservation_id}")
```

### With Google Places Integration
```python
async with AsyncBookalimo(
    credentials=credentials,
    google_places_api_key="your-google-key"
) as client:
    # Find locations
    pickup_results = await client.places.search("JFK Airport")
    dropoff_results = await client.places.search("Empire State Building")
    
    # Convert to booking locations and proceed with booking...
```

### Error Handling
```python
from bookalimo.exceptions import BookalimoHTTPError, BookalimoTimeout

try:
    quote = await client.pricing.quote(...)
except BookalimoTimeout:
    print("Request timed out - check network connection")
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed - check credentials")
    else:
        print(f"API error {e.status_code}: {e}")
except BookalimoError as e:
    print(f"General SDK error: {e}")
```

## Version Information

This documentation covers Bookalimo Python SDK v1.0.0. For the latest version and updates, see the [changelog](../changelog.md).

## Support

- **Documentation**: Complete guides and examples
- **GitHub Issues**: Bug reports and feature requests
- **API Reference**: This comprehensive reference documentation