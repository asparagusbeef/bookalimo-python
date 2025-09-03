"""Tests for bookalimo.models."""

from bookalimo import (
    create_address_location,
    create_airport_location,
    create_credentials,
)
from bookalimo.models import Credentials, LocationType, RateType


def test_credentials_hash() -> None:
    """Test credential hash generation."""
    password = "test_password"
    user_id = "TEST123"

    creds = create_credentials(user_id, password)

    # Verify the hash is generated correctly
    expected = Credentials.create_hash(password, user_id)
    assert creds.password_hash == expected


def test_rate_type_enum() -> None:
    """Test RateType enum values."""
    assert RateType.P2P.value == 0
    assert RateType.HOURLY.value == 1


def test_location_type_enum() -> None:
    """Test LocationType enum values."""
    assert LocationType.ADDRESS.value == 0
    assert LocationType.AIRPORT.value == 1


def test_create_airport_location() -> None:
    """Test airport location creation."""
    location = create_airport_location("JFK", "New York")

    assert location.type == LocationType.AIRPORT
    assert location.airport is not None
    assert location.airport.iata_code == "JFK"


def test_create_address_location() -> None:
    """Test address location creation."""
    location = create_address_location("123 Main St")

    assert location.type == LocationType.ADDRESS
    assert location.address is not None
    assert location.address.place_name == "123 Main St"
