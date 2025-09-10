# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-09-09

### Fixed
- Google Places API key handling in geocoding requests
- Optional field handling in Google Places models

### Changed
- **BREAKING**: All service methods now accept request objects directly instead of individual parameters
  - `pricing.quote(PriceRequest)` instead of `pricing.quote(rate_type, date_time, pickup, ...)`
  - `pricing.update_details(DetailsRequest)` instead of `pricing.update_details(token, **details)`
  - `reservations.book(BookRequest)` instead of `reservations.book(token, method=...)`
  - `reservations.edit(EditReservationRequest)` instead of `reservations.edit(confirmation, **changes)`
- **BREAKING**: Schema architecture cleanup for better maintainability
  - Moved `EditReservationRequest` definition from shared.py to requests.py
  - Removed duplicate `EditReservationRequest` from responses.py
  - Added `ReservationData` for reservation data in API responses
  - Eliminated confusing inheritance patterns and improved separation of concerns
- **BREAKING**: Complete schema architecture overhaul - request models serialize to camelCase, response models to snake_case
- **BREAKING**: Schema imports updated to `from bookalimo.schemas import`
- **BREAKING**: Method calls updated from `search_text` to `search`
- **BREAKING**: Removed `ApiModel` class - use `RequestModel`/`ResponseModel`
- **BREAKING**: `PriceData` renamed to `CarClassPrice`
- Refactored sync/async clients to reduce code duplication
- Redacted httpx logging plain urls with sensitive parameters
- Updated documentation structure and content

## [1.0.1] - 2025-09-08

### Added
- Enhanced Google Places integration with `autocomplete()` and `resolve_airport()` methods
- New `SearchTextRequest` model for advanced search filtering
- Airport resolution with confidence scoring
- Flexible field mask validation

### Changed
- **BREAKING**: `GooglePlace` model renamed from `Place`
- **BREAKING**: Removed `iata_code` field (use `resolve_airport()` instead)
- Enhanced search and get methods with more flexible input options
- Improved schema organization and enum handling

## [1.0.0] - 2025-09-07

### Changed
- **MAJOR REFACTOR**: Complete SDK architecture overhaul
- New client interface: `Bookalimo` (sync) and `AsyncBookalimo` (async)
- Services-based architecture: `client.reservations.*` and `client.pricing.*`
- Google Places moved to optional integration with `pip install bookalimo[places]`
- Clean exception hierarchy and improved error handling

### Added
- Sync client support alongside async client
- Resource-style API methods
- Comprehensive retry logic with exponential backoff
- Enhanced logging system

### Removed
- Old `BookALimo` wrapper class
- Factory helper methods (use models directly)

## [0.1.5] - 2025-09-04

### Fixed
- Type hints for logging decorator

## [0.1.4] - 2025-09-02

### Added
- Logging handling and documentation

### Fixed
- Base URL typo

## [0.1.3] - 2025-09-02

### Changed
- Moved `BookalimoError` to separate `exceptions.py` module
- Updated README.md

## [0.1.2] - 2025-09-02

### Fixed
- Minor fixes

## [0.1.1] - 2025-09-02

### Fixed
- Minor fixes

## [0.1.0] - 2024-09-02

### Added
- Initial release of bookalimo Python SDK
- Support for Book-A-Limo API endpoints
- Pydantic models and async support
- Type hints and error handling
- Documentation
