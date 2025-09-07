"""
Google Places API integration for Bookalimo.

This integration requires the 'places' extra:
    pip install bookalimo[places]

Examples:
    # Async client
    from bookalimo.integrations.google_places import AsyncGooglePlaces

    async with AsyncGooglePlaces() as places:
        results = await places.autocomplete("Empire State Building")

    # Sync client
    from bookalimo.integrations.google_places import GooglePlaces

    with GooglePlaces() as places:
        results = places.autocomplete("Empire State Building")
"""

try:
    from .client_async import AsyncGooglePlaces
    from .client_sync import GooglePlaces

    __all__ = ["AsyncGooglePlaces", "GooglePlaces"]

except ImportError as e:
    raise ImportError(
        "Google Places integration requires the 'places' extra. "
        "Install with: pip install bookalimo[places]"
    ) from e
