# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-01-15

### Added
- **Schemas**: Enhanced `ApiModel` serialization with flexible case conversion options
- **Schemas**: Added `snake_case` context option for forcing snake_case output
- **Schemas**: Deep snake_case conversion support for nested data structures
- **Exports**: Added missing exports (`GooglePlace`, `PriceLevel`, `FieldMaskInput`, `BusinessStatus`) to main schema module

### Changed
- **Google Places**: Geocoding API now properly includes API key in request parameters
- **Google Places**: Both sync and async clients now store API key as instance variable for better access
- **Schemas**: `CardHolderType` enum values updated with correct API mappings (`CORPORATE=0`, `AGENCY=1`, `THIRD_PARTY=2`, `SAME_AS_PASSENGER=3`)
- **Schemas**: Enhanced `Address.google_geocode` field documentation with common usage mistake warning
- **Schemas**: `LocalizedText.language_code` field is now optional
- **Common**: `build_get_place_request` now uses enum name serialization for better API compatibility
- **CI**: Re-enabled performance and slow integration tests in GitHub Actions workflow

### Fixed
- **Documentation**: Clarified that Google Application Default Credentials (ADC) is not yet implemented across all documentation
- **Google Places**: Fixed geocoding API authentication by properly passing API key in query parameters

## [1.0.1] - 2025-09-08

### Added
- **Schemas**: New `FieldMaskInput` type for flexible field mask validation
- **Google Places**: `autocomplete()` now accepts either a string input or a `AutocompletePlacesRequest` object
- **Google Places**: New `resolve_airport()` method for advanced airport resolution with confidence scoring
- **Google Places**: Support for `SearchTextRequest` objects in `search()` method for advanced filtering
- **Schemas**: New `ResolvedAirport` model with text and proximity confidence scores
- **Schemas**: New `RankPreference` enum for search result ranking (`DISTANCE`, `RELEVANCE`)
- **Schemas**: New `SearchTextRequest` model with comprehensive search parameters
- **Schemas**: New `SearchTextResponse` model for text search API responses
-
### Changed
- **BREAKING**: `GooglePlace` model renamed from `Place` in `place.py` for clarity
- **BREAKING**: Removed `iata_code` field from `Place` model (use `resolve_airport()` instead)
- **Google Places**: Enhanced `search()` method now accepts either simple queries or `SearchTextRequest` objects
- **Google Places**: Updated `get()` method to accept optional `GetPlaceRequest` objects instead of raw place IDs for better flexibility
- **Google Places**: Removed the restrictive `Fields` and `PlaceListFields` types and replaced them with `FieldMaskInput` and `FieldPath` for better flexibility
- **Schemas**: `PlaceType` converted to string enum (`StrEnum`)
- **Schemas**: `PriceLevel` and `BusinessStatus` converted to integer enums (`IntEnum`)
- **Schemas**: Enhanced `AddressDescriptor` model with detailed landmark and area information
- **Common**: Moved shared utilities from client files to `common.py` for better code organization
- **Documentation**: Updated CI to have docs share README.md, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, and removed index.md from docs folder
- **Refactor**: Common code from `/integrations/google_places/client_async.py` and `/integrations/google_places/client_sync.py` to `/integrations/google_places/common.py` + created `transports.py` for protocol definition.

## [1.0.0] - 2025-09-07

### Changed
- **MAJOR REFACTOR**: Complete SDK architecture overhaul for clean, production-ready design
- New client interface: `Bookalimo` (sync) and `AsyncBookalimo` (async) with resource-style services
- Services-based architecture: `client.reservations.*` and `client.pricing.*` methods
- Moved to clean transport layer with proper sync/async implementations
- Reorganized schemas: `schemas/booking.py` and `schemas/places/` structure
- Google Places moved to optional `integrations/google_places` with `pip install bookalimo[places]`
- Clean exception hierarchy: `BookalimoError`, `BookalimoHTTPError`, `BookalimoTimeout`, etc.
- Removed factory helper methods (users import and use models directly - more Pythonic)
- Simplified logging - uses standard Python logging, respects user configuration

### Added
- Sync client support alongside existing async client
- Resource-style API: `client.reservations.list()`, `client.pricing.quote()`, etc.
- Comprehensive retry logic with exponential backoff and jitter
- Optional Google Places integration behind `[places]` extra
- `BookalimoValidationError` for aggregated, field-level validation errors.
- Logging improvements and `get_logger()` export; optional `http_timeout` on `Bookalimo`.

### Removed
- Old `BookALimo` wrapper class (replaced with `AsyncBookalimo` and `Bookalimo`)
- Factory helper methods (`create_address_location`, etc.) - use models directly
- Authenticated model duplicates (simplified credential injection)
- `enable_debug_logging`/`disable_debug_logging` functions -> use `BOOKALIMO_LOG_LEVEL` environment variable

## [0.1.5] - 2025-09-04

### Fixed
- Fix type hints for logging decorator

## [0.1.4] - 2025-09-02

### Added
- logging handling + documentation

### Fixed
- Fix typo in base_url

## [0.1.3] - 2025-09-02

### Changed
- Moved `BookalimoError` to a separate `exceptions.py` module.
- Updated README.md.

## [0.1.2] - 2025-09-02

### Fixed
- Minor fixes

## [0.1.1] - 2025-09-02

### Fixed
- Minor fixes

## [0.1.0] - 2024-09-02

### Added
- Initial release of bookalimo Python SDK
- Support for all Book-A-Limo API endpoints
- Pydantic models for request/response validation
- Async/await support with httpx
- Complete type hints
- Error handling and custom exceptions
- Documentation with MkDocs
