"""Tests for Pydantic schemas and data validation."""

import pytest
from pydantic import ValidationError

from bookalimo.schemas.base import ApiModel
from bookalimo.schemas.booking import (
    Address,
    Airport,
    BookRequest,
    City,
    CreditCard,
    EditableReservationRequest,
    GetReservationRequest,
    ListReservationsRequest,
    Location,
    LocationType,
    PriceRequest,
    PriceResponse,
    RateType,
)


class TestLocation:
    """Tests for Location schema."""

    def test_address_location_valid(self):
        """Test valid address location."""
        location = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="123 Main St",
                street_name="Main St",
                building="123",
                suite="Apt 4B",
                zip="10001",
                city=City(
                    city_name="New York",
                    country_code="US",
                    state_code="NY",
                    state_name="New York",
                ),
            ),
        )

        assert location.type == LocationType.ADDRESS
        assert location.address is not None
        assert location.address.place_name == "123 Main St"
        assert location.address.city is not None
        assert location.address.city.city_name == "New York"
        assert location.address.city.state_code == "NY"
        assert location.address.city.country_code == "US"

    def test_airport_location_valid(self):
        """Test valid airport location."""
        location = Location(
            type=LocationType.AIRPORT,
            airport=Airport(iata_code="JFK", country_code="US", state_code="NY"),
        )

        assert location.type == LocationType.AIRPORT
        assert location.airport is not None
        assert location.airport.iata_code == "JFK"
        assert location.airport.country_code == "US"

    def test_location_address_required_when_type_address(self):
        """Test that address is required when type is ADDRESS."""
        with pytest.raises(
            ValidationError, match="Address is required when type is ADDRESS"
        ):
            Location(type=LocationType.ADDRESS)

    def test_location_airport_required_when_type_airport(self):
        """Test that airport is required when type is AIRPORT."""
        with pytest.raises(
            ValidationError, match="Airport is required when type is AIRPORT"
        ):
            Location(type=LocationType.AIRPORT)

    def test_location_validation_with_wrong_type_combo(self):
        """Test validation fails when address provided for airport type."""
        with pytest.raises(ValidationError):
            Location(
                type=LocationType.AIRPORT,
                address=Address(
                    place_name="Test Address",
                    city=City(
                        city_name="Test City", country_code="US", state_code="NY"
                    ),
                ),
            )


class TestAddress:
    """Tests for Address schema."""

    def test_address_with_google_geocode(self):
        """Test address with Google geocode data."""
        geocode_data = {
            "results": [{"formatted_address": "123 Main St, New York, NY, USA"}]
        }
        address = Address(place_name="123 Main St", google_geocode=geocode_data)

        assert address.place_name == "123 Main St"
        assert address.google_geocode == geocode_data

    def test_address_with_city_object(self):
        """Test address with City object."""
        address = Address(
            place_name="Test Location",
            city=City(
                city_name="New York",
                country_code="US",
                state_code="NY",
                state_name="New York",
            ),
        )

        assert address.place_name == "Test Location"
        assert address.city is not None
        assert address.city.city_name == "New York"

    def test_address_requires_place_name_or_street_name(self):
        """Test that address requires either place_name or street_name."""
        with pytest.raises(
            ValidationError, match="Either place_name or street_name must be provided"
        ):
            Address(
                city=City(city_name="Test City", country_code="US", state_code="NY")
            )

    def test_address_requires_city_or_geocode(self):
        """Test that address requires either city or google_geocode."""
        with pytest.raises(
            ValidationError, match="Either city or google_geocode must be provided"
        ):
            Address(place_name="Test Place")

    def test_address_cannot_have_both_city_and_geocode(self):
        """Test that address cannot have both city and google_geocode."""
        with pytest.raises(
            ValidationError, match="Only one of city or google_geocode must be provided"
        ):
            Address(
                place_name="Test Place",
                city=City(city_name="New York", country_code="US", state_code="NY"),
                google_geocode={"test": "data"},
            )


class TestAirport:
    """Tests for Airport schema."""

    def test_airport_minimal(self):
        """Test airport with minimal required fields."""
        airport = Airport(iata_code="JFK")

        assert airport.iata_code == "JFK"
        assert airport.country_code is None
        assert airport.state_code is None

    def test_airport_with_optional_fields(self):
        """Test airport with optional fields."""
        airport = Airport(
            iata_code="LAX",
            country_code="US",
            state_code="CA",
            airline_iata_code="UA",
            flight_number="UA123",
            terminal="7",
        )

        assert airport.iata_code == "LAX"
        assert airport.country_code == "US"
        assert airport.state_code == "CA"
        assert airport.airline_iata_code == "UA"
        assert airport.flight_number == "UA123"
        assert airport.terminal == "7"

    def test_airport_invalid_iata_code(self):
        """Test airport with invalid IATA code."""
        with pytest.raises(ValidationError, match="Invalid IATA code"):
            Airport(iata_code="INVALID")


class TestCity:
    """Tests for City schema."""

    def test_city_us_valid(self):
        """Test valid US city."""
        city = City(
            city_name="New York",
            country_code="US",
            state_code="NY",
            state_name="New York",
        )

        assert city.city_name == "New York"
        assert city.country_code == "US"
        assert city.state_code == "NY"
        assert city.state_name == "New York"

    def test_city_international_valid(self):
        """Test valid international city."""
        city = City(city_name="Toronto", country_code="CA")

        assert city.city_name == "Toronto"
        assert city.country_code == "CA"
        assert city.state_code is None

    def test_city_invalid_country_code(self):
        """Test city with invalid country code."""
        with pytest.raises(ValidationError, match="Invalid country code"):
            City(city_name="Test City", country_code="INVALID")


class TestRateType:
    """Tests for RateType enum."""

    def test_rate_type_values(self):
        """Test all rate type enum values."""
        assert RateType.P2P.value == 0
        assert RateType.HOURLY.value == 1
        assert RateType.DAILY.value == 2
        assert RateType.TOUR.value == 3
        assert RateType.ROUND_TRIP.value == 4
        assert RateType.RT_HALF.value == 5

    def test_rate_type_in_schema(self):
        """Test rate type usage in schema."""
        request = PriceRequest(
            rate_type=RateType.HOURLY,
            date_time="09/10/2025 03:00 PM",
            pickup=Location(
                type=LocationType.ADDRESS,
                address=Address(
                    place_name="Test Pickup",
                    city=City(city_name="City", country_code="US", state_code="CA"),
                ),
            ),
            dropoff=Location(
                type=LocationType.AIRPORT, airport=Airport(iata_code="TST")
            ),
            passengers=2,
            luggage=1,
        )

        assert request.rate_type == RateType.HOURLY


class TestPriceRequest:
    """Tests for PriceRequest schema."""

    @pytest.fixture
    def valid_pickup(self):
        return Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="123 Test St",
                city=City(city_name="Test City", country_code="US", state_code="CA"),
            ),
        )

    @pytest.fixture
    def valid_dropoff(self):
        return Location(type=LocationType.AIRPORT, airport=Airport(iata_code="TST"))

    def test_price_request_minimal(self, valid_pickup, valid_dropoff):
        """Test price request with minimal required fields."""
        request = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=valid_pickup,
            dropoff=valid_dropoff,
            passengers=1,
            luggage=0,
        )

        assert request.rate_type == RateType.P2P
        assert request.date_time == "09/10/2025 03:00 PM"
        assert request.pickup == valid_pickup
        assert request.dropoff == valid_dropoff
        assert request.passengers == 1
        assert request.luggage == 0

    def test_price_request_with_optional_fields(self, valid_pickup, valid_dropoff):
        """Test price request with all optional fields."""
        request = PriceRequest(
            rate_type=RateType.HOURLY,
            date_time="09/10/2025 03:00 PM",
            pickup=valid_pickup,
            dropoff=valid_dropoff,
            passengers=4,
            luggage=2,
            hours=3,
            car_class_code="SUV",
            pets=1,
            car_seats=2,
            boosters=1,
            infants=1,
            customer_comment="Please arrive 15 minutes early",
        )

        assert request.hours == 3
        assert request.car_class_code == "SUV"
        assert request.pets == 1
        assert request.car_seats == 2
        assert request.boosters == 1
        assert request.infants == 1
        assert request.customer_comment == "Please arrive 15 minutes early"


class TestPriceResponse:
    """Tests for PriceResponse schema."""

    def test_price_response_minimal(self):
        """Test price response with minimal required fields."""
        response = PriceResponse(token="test-token-123", prices=[])

        assert response.token == "test-token-123"
        assert response.prices == []

    def test_price_response_with_prices(self):
        """Test price response with price data."""
        from bookalimo.schemas.booking import Price

        price = Price(
            car_class="SEDAN",
            car_description="Standard Sedan",
            max_passengers=4,
            max_luggage=2,
            price=150.00,
            price_default=175.00,
            image128="http://example.com/sedan128.png",
            image256="http://example.com/sedan256.png",
            image512="http://example.com/sedan512.png",
            meet_greets=[],
        )

        response = PriceResponse(token="test-token-456", prices=[price])

        assert response.token == "test-token-456"
        assert len(response.prices) == 1
        assert response.prices[0].car_class == "SEDAN"
        assert response.prices[0].price == 150.00


class TestCreditCard:
    """Tests for CreditCard schema."""

    def test_credit_card_valid(self):
        """Test valid credit card."""
        card = CreditCard(
            number="4111111111111111",
            expiration="12/25",
            cvv="123",
            card_holder="John Doe",
            zip="10001",
        )

        assert card.number == "4111111111111111"
        assert card.expiration == "12/25"
        assert card.cvv == "123"
        assert card.card_holder == "John Doe"
        assert card.zip == "10001"

    def test_credit_card_amex_cvv(self):
        """Test American Express card with 4-digit CVV."""
        card = CreditCard(
            number="378282246310005",  # Amex test number
            expiration="12/25",
            cvv="1234",  # 4-digit CVV for Amex
            card_holder="John Doe",
            zip="10001",
        )

        assert card.cvv == "1234"

    def test_credit_card_missing_required_fields(self):
        """Test credit card missing required fields."""
        with pytest.raises(ValidationError):
            CreditCard(
                number="4111111111111111",
                expiration="12/25",
                # Missing cvv, card_holder
            )  # type: ignore


class TestBookRequest:
    """Tests for BookRequest schema."""

    @pytest.fixture
    def valid_credit_card(self):
        return CreditCard(
            number="4111111111111111",
            expiration="12/25",
            cvv="123",
            card_holder="John Doe",
            zip="10001",
        )

    def test_book_request_with_credit_card(self, valid_credit_card):
        """Test book request with credit card payment."""
        request = BookRequest(token="booking-token-123", credit_card=valid_credit_card)

        assert request.token == "booking-token-123"
        assert request.credit_card == valid_credit_card
        assert request.method is None

    def test_book_request_with_charge_method(self):
        """Test book request with charge account payment."""
        request = BookRequest(token="booking-token-456", method="charge")

        assert request.token == "booking-token-456"
        assert request.method == "charge"
        assert request.credit_card is None

    def test_book_request_validation_requires_payment_method(self):
        """Test book request validation requires either method or credit_card."""
        with pytest.raises(
            ValidationError,
            match="Either method='charge' or credit_card must be provided",
        ):
            BookRequest(
                token="booking-token-789"
                # No payment method provided
            )


class TestReservationSchemas:
    """Tests for reservation-related schemas."""

    def test_list_reservations_request(self):
        """Test list reservations request."""
        # Default (active reservations)
        request = ListReservationsRequest()
        assert request.is_archive is False

        # Archived reservations
        request_archived = ListReservationsRequest(is_archive=True)
        assert request_archived.is_archive is True

    def test_get_reservation_request(self):
        """Test get reservation request."""
        request = GetReservationRequest(confirmation="TEST123")
        assert request.confirmation == "TEST123"

    def test_edit_reservation_request_cancel(self):
        """Test edit reservation request for cancellation."""
        request = EditableReservationRequest(
            confirmation="CANCEL123", is_cancel_request=True
        )

        assert request.confirmation == "CANCEL123"
        assert request.is_cancel_request is True

    def test_edit_reservation_request_modify(self):
        """Test edit reservation request for modification."""
        request = EditableReservationRequest(
            confirmation="MODIFY123",
            is_cancel_request=False,
            passengers=4,
            luggage=2,
            pickup_time="04:00 PM",
            other="Special instructions",
        )

        assert request.confirmation == "MODIFY123"
        assert request.is_cancel_request is False
        assert request.passengers == 4
        assert request.luggage == 2
        assert request.pickup_time == "04:00 PM"
        assert request.other == "Special instructions"


class TestSchemaValidation:
    """Tests for general schema validation behavior."""

    def test_model_dump_excludes_none(self):
        """Test that model_dump excludes None values when configured."""
        pickup = Location(
            type=LocationType.ADDRESS,
            address=Address(
                place_name="Test",
                city=City(city_name="City", country_code="US", state_code="CA"),
            ),
        )

        dropoff = Location(type=LocationType.AIRPORT, airport=Airport(iata_code="TST"))

        request = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=pickup,
            dropoff=dropoff,
            passengers=2,
            luggage=1,
            hours=None,  # Should be excluded
            customer_comment="Valid comment",
        )

        dumped = request.model_dump(exclude_none=True)

        assert "hours" not in dumped
        assert "customerComment" in dumped
        assert dumped["customerComment"] == "Valid comment"

    def test_api_model_base_functionality(self):
        """Test ApiModel base class functionality."""

        class TestModel(ApiModel):
            name: str
            value: int = 10

        model = TestModel(name="test")
        assert model.name == "test"
        assert model.value == 10

        # Test model_dump
        dumped = model.model_dump()
        assert dumped == {"name": "test", "value": 10}

    def test_schema_serialization_consistency(self):
        """Test that schemas can be serialized and deserialized consistently."""
        original_location = Location(
            type=LocationType.AIRPORT,
            airport=Airport(iata_code="TST", country_code="US", state_code="CA"),
        )

        # Serialize to dict
        data = original_location.model_dump()

        # Deserialize from dict
        restored_location = Location.model_validate(data)

        assert restored_location == original_location
        assert restored_location.type == original_location.type
        assert restored_location.airport is not None
        assert original_location.airport is not None
        assert (
            restored_location.airport.iata_code == original_location.airport.iata_code
        )


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string_fields_in_address(self):
        """Test handling of empty string fields in address."""
        with pytest.raises(ValidationError):
            Address(
                place_name="",  # Empty place_name should be invalid
                city=City(city_name="City", country_code="US", state_code="CA"),
            )

    def test_unicode_characters_in_address(self):
        """Test handling of unicode characters in address."""
        address = Address(
            place_name="Café París",  # Unicode characters
            city=City(city_name="São Paulo", country_code="BR"),
        )

        assert address.place_name == "Café París"
        assert address.city is not None
        assert address.city.city_name == "São Paulo"

    def test_special_characters_in_address(self):
        """Test handling of special characters in address."""
        address = Address(
            place_name="123 Main St. #4B",  # Special characters
            street_name="Main St.",
            suite="Apt #4B (Rear)",
            city=City(
                city_name="New York",
                country_code="US",
                state_code="NY",
                state_name="New York",
            ),
        )
        assert address.place_name is not None
        assert address.city is not None
        assert address.suite is not None
        assert "#" in address.place_name
        assert "(" in address.suite
        assert ")" in address.suite
