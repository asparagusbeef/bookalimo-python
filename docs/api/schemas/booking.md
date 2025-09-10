# Booking Schemas

Data models for transportation booking operations.

## Enums

- `RateType` - P2P: 0, HOURLY: 1, DAILY: 2, TOUR: 3, ROUND_TRIP: 4, RT_HALF: 5
- `LocationType` - ADDRESS: 0, AIRPORT: 1, TRAIN_STATION: 2, CRUISE: 3
- `ReservationStatus` - ACTIVE: None, NO_SHOW: 0, CANCELED: 1, LATE_CANCELED: 2
- `CardHolderType` - CORPORATE: 0, AGENCY: 1, THIRD_PARTY: 2, SAME_AS_PASSENGER: 3
- `MeetGreetType` - Meet & greet options for airport pickups
- `RewardType` - Reward program types (e.g., UNITED_MILEAGEPLUS: 0)

## Location Models

### City
Geographic location with country/state validation. Requires `city_name` and `country_code` (ISO 3166-1 alpha-2).

### Address
Street address or venue location. Either `google_geocode` (preferred) or `city` required. Supports venue names via `place_name`.

### Airport
Airport with IATA code and optional flight details. Requires valid 3-letter `iata_code` with optional terminal and flight info.

### Location
Union of address or airport locations. Use `type` field to specify `LocationType.ADDRESS` or `LocationType.AIRPORT`.

## Booking Data Models

### Passenger
Passenger information with `first_name`, `last_name`, optional `email`, and `phone` (E164 format recommended).

### CreditCard
Payment information with `number`, `expiration` (MM/YY), `cvv`, `card_holder`, optional `zip` and `holder_type`.

### Stop
Additional stop with `description` (address/place name) and `is_en_route` boolean flag.

### Account
Travel agency or corporate account info with `id` and optional booker details.

## Request/Response Models

- `PriceRequest` / `PriceResponse` - pricing operations
- `DetailsRequest` / `DetailsResponse` - detail updates
- `BookRequest` / `BookResponse` - reservation booking
- `ListReservationsRequest` / `ListReservationsResponse` - reservation listing
- `GetReservationRequest` / `GetReservationResponse` - reservation details
- `EditReservationRequest` / `EditReservationResponse` - modifications
