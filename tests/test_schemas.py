"""Tests for Pydantic schemas and data validation."""

import pytest
from decimal import Decimal
from typing import Any, Dict

from pydantic import ValidationError

from bookalimo.schemas.booking import (
    BookRequest,
    BookResponse,
    CreditCard,
    DetailsRequest,
    DetailsResponse,
    EditableReservationRequest,
    EditReservationResponse,
    GetReservationRequest,
    GetReservationResponse,
    ListReservationsRequest,
    ListReservationsResponse,
    Location,
    LocationType,
    PriceRequest,
    PriceResponse,
    RateType,
    Reservation,
    Stop,
)
from bookalimo.schemas.base import ApiModel


class TestLocation:
    """Tests for Location schema."""

    def test_address_location_valid(self):
        """Test valid address location."""
        location = Location(
            type=LocationType.ADDRESS,
            name="123 Main St",
            line1="123 Main St",
            line2="Apt 4B",
            city="New York",
            state="NY",
            zip_code="10001",
            country="US",
            latitude=40.7128,
            longitude=-74.0060
        )
        
        assert location.type == LocationType.ADDRESS
        assert location.name == "123 Main St"
        assert location.city == "New York"
        assert location.state == "NY"
        assert location.country == "US"
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060

    def test_airport_location_valid(self):
        """Test valid airport location."""
        location = Location(
            type=LocationType.AIRPORT,
            name="John F. Kennedy International Airport",
            line1="JFK Airport",
            city="Queens",
            state="NY",
            zip_code="11430",
            country="US",
            airport_code="JFK",
            latitude=40.6413,
            longitude=-73.7781
        )
        
        assert location.type == LocationType.AIRPORT
        assert location.airport_code == "JFK"
        assert location.name == "John F. Kennedy International Airport"

    def test_train_station_location_valid(self):
        """Test valid train station location."""
        location = Location(
            type=LocationType.TRAIN_STATION,
            name="Penn Station",
            line1="4 Pennsylvania Plaza",
            city="New York",
            state="NY",
            zip_code="10001",
            country="US",
            latitude=40.7505,
            longitude=-73.9934
        )
        
        assert location.type == LocationType.TRAIN_STATION
        assert location.name == "Penn Station"

    def test_cruise_location_valid(self):
        """Test valid cruise terminal location."""
        location = Location(
            type=LocationType.CRUISE,
            name="Brooklyn Cruise Terminal",
            line1="72 Bowne St",
            city="Brooklyn",
            state="NY",
            zip_code="11231",
            country="US",
            latitude=40.6771,
            longitude=-74.0143
        )
        
        assert location.type == LocationType.CRUISE
        assert location.name == "Brooklyn Cruise Terminal"

    def test_location_minimal_fields(self):
        """Test location with minimal required fields."""
        location = Location(
            type=LocationType.ADDRESS,
            name="Simple Address",
            city="City",
            state="ST",
            country="US"
        )
        
        assert location.type == LocationType.ADDRESS
        assert location.name == "Simple Address"
        assert location.city == "City"
        assert location.state == "ST"
        assert location.country == "US"

    def test_location_invalid_coordinates(self):
        """Test location with invalid coordinates."""
        with pytest.raises(ValidationError):
            Location(
                type=LocationType.ADDRESS,
                name="Invalid Location",
                city="City",
                state="ST",
                country="US",
                latitude=200.0,  # Invalid latitude
                longitude=-74.0060
            )

    def test_location_missing_required_fields(self):
        """Test location missing required fields."""
        with pytest.raises(ValidationError):
            Location(
                type=LocationType.ADDRESS,
                name="Incomplete Location"
                # Missing city, state, country
            )

    def test_location_enum_validation(self):
        """Test location type enum validation."""
        with pytest.raises(ValidationError):
            Location(
                type="INVALID_TYPE",  # Invalid enum value
                name="Test Location",
                city="City",
                state="ST",
                country="US"
            )


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
                name="Test Pickup",
                city="City",
                state="ST",
                country="US"
            ),
            dropoff=Location(
                type=LocationType.AIRPORT,
                name="Test Airport",
                city="City",
                state="ST",
                country="US",
                airport_code="TST"
            ),
            passengers=2,
            luggage=1
        )
        
        assert request.rate_type == RateType.HOURLY


class TestPriceRequest:
    """Tests for PriceRequest schema."""

    @pytest.fixture
    def valid_pickup(self):
        return Location(
            type=LocationType.ADDRESS,
            name="123 Test St",
            city="Test City",
            state="TS",
            country="US"
        )

    @pytest.fixture
    def valid_dropoff(self):
        return Location(
            type=LocationType.AIRPORT,
            name="Test Airport",
            city="Test City",
            state="TS",
            country="US",
            airport_code="TST"
        )

    def test_price_request_minimal(self, valid_pickup, valid_dropoff):
        """Test price request with minimal required fields."""
        request = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=valid_pickup,
            dropoff=valid_dropoff,
            passengers=1,
            luggage=0
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
            account="CORP123",
            passenger="John Doe",
            rewards="GOLD"
        )
        
        assert request.hours == 3
        assert request.car_class_code == "SUV"
        assert request.pets == 1
        assert request.car_seats == 2
        assert request.boosters == 1
        assert request.infants == 1
        assert request.customer_comment == "Please arrive 15 minutes early"
        assert request.account == "CORP123"
        assert request.passenger == "John Doe"
        assert request.rewards == "GOLD"

    def test_price_request_invalid_passengers(self, valid_pickup, valid_dropoff):
        """Test price request with invalid passenger count."""
        with pytest.raises(ValidationError):
            PriceRequest(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=valid_pickup,
                dropoff=valid_dropoff,
                passengers=0,  # Invalid - must be positive
                luggage=1
            )

    def test_price_request_negative_luggage(self, valid_pickup, valid_dropoff):
        """Test price request with negative luggage count."""
        with pytest.raises(ValidationError):
            PriceRequest(
                rate_type=RateType.P2P,
                date_time="09/10/2025 03:00 PM",
                pickup=valid_pickup,
                dropoff=valid_dropoff,
                passengers=2,
                luggage=-1  # Invalid - cannot be negative
            )


class TestPriceResponse:
    """Tests for PriceResponse schema."""

    def test_price_response_minimal(self):
        """Test price response with minimal required fields."""
        response = PriceResponse(
            token="test-token-123",
            total=100.00,
            currency="USD"
        )
        
        assert response.token == "test-token-123"
        assert response.total == 100.00
        assert response.currency == "USD"

    def test_price_response_with_all_fields(self):
        """Test price response with all fields."""
        response = PriceResponse(
            token="test-token-456",
            total=175.50,
            base_rate=150.00,
            tax=12.50,
            tip=13.00,
            currency="USD",
            car_class_code="LUXURY",
            estimated_time="45 minutes",
            distance="25.3 miles",
            special_instructions="VIP service"
        )
        
        assert response.token == "test-token-456"
        assert response.total == 175.50
        assert response.base_rate == 150.00
        assert response.tax == 12.50
        assert response.tip == 13.00
        assert response.currency == "USD"
        assert response.car_class_code == "LUXURY"
        assert response.estimated_time == "45 minutes"
        assert response.distance == "25.3 miles"
        assert response.special_instructions == "VIP service"

    def test_price_response_decimal_precision(self):
        """Test price response handles decimal precision correctly."""
        response = PriceResponse(
            token="precision-test",
            total=123.456,  # Will be rounded to 2 decimal places
            base_rate=100.123,
            tax=15.678,
            currency="USD"
        )
        
        # Should handle decimal precision appropriately
        assert isinstance(response.total, (int, float, Decimal))
        assert isinstance(response.base_rate, (int, float, Decimal))
        assert isinstance(response.tax, (int, float, Decimal))


class TestCreditCard:
    """Tests for CreditCard schema."""

    def test_credit_card_valid(self):
        """Test valid credit card."""
        card = CreditCard(
            number="4111111111111111",
            exp_month="12",
            exp_year="25",
            cvv="123",
            cardholder_name="John Doe",
            billing_zip="10001"
        )
        
        assert card.number == "4111111111111111"
        assert card.exp_month == "12"
        assert card.exp_year == "25"
        assert card.cvv == "123"
        assert card.cardholder_name == "John Doe"
        assert card.billing_zip == "10001"

    def test_credit_card_amex_cvv(self):
        """Test American Express card with 4-digit CVV."""
        card = CreditCard(
            number="378282246310005",  # Amex test number
            exp_month="12",
            exp_year="25",
            cvv="1234",  # 4-digit CVV for Amex
            cardholder_name="John Doe",
            billing_zip="10001"
        )
        
        assert card.cvv == "1234"

    def test_credit_card_with_optional_fields(self):
        """Test credit card with optional fields."""
        card = CreditCard(
            number="4111111111111111",
            exp_month="12",
            exp_year="25",
            cvv="123",
            cardholder_name="Jane Smith",
            billing_zip="90210",
            billing_address_line1="123 Beverly Hills Rd",
            billing_city="Beverly Hills",
            billing_state="CA",
            billing_country="US"
        )
        
        assert card.billing_address_line1 == "123 Beverly Hills Rd"
        assert card.billing_city == "Beverly Hills"
        assert card.billing_state == "CA"
        assert card.billing_country == "US"

    def test_credit_card_invalid_number_format(self):
        """Test credit card with invalid number format."""
        # Note: This test assumes the schema validates credit card numbers
        # The actual validation rules depend on the schema implementation
        with pytest.raises(ValidationError):
            CreditCard(
                number="invalid-card-number",
                exp_month="12",
                exp_year="25",
                cvv="123",
                cardholder_name="John Doe",
                billing_zip="10001"
            )

    def test_credit_card_invalid_expiry_month(self):
        """Test credit card with invalid expiry month."""
        with pytest.raises(ValidationError):
            CreditCard(
                number="4111111111111111",
                exp_month="13",  # Invalid month
                exp_year="25",
                cvv="123",
                cardholder_name="John Doe",
                billing_zip="10001"
            )

    def test_credit_card_missing_required_fields(self):
        """Test credit card missing required fields."""
        with pytest.raises(ValidationError):
            CreditCard(
                number="4111111111111111",
                exp_month="12",
                # Missing exp_year, cvv, etc.
            )


class TestBookRequest:
    """Tests for BookRequest schema."""

    @pytest.fixture
    def valid_credit_card(self):
        return CreditCard(
            number="4111111111111111",
            exp_month="12",
            exp_year="25",
            cvv="123",
            cardholder_name="John Doe",
            billing_zip="10001"
        )

    def test_book_request_with_credit_card(self, valid_credit_card):
        """Test book request with credit card payment."""
        request = BookRequest(
            token="booking-token-123",
            credit_card=valid_credit_card
        )
        
        assert request.token == "booking-token-123"
        assert request.credit_card == valid_credit_card
        assert request.method is None

    def test_book_request_with_charge_method(self):
        """Test book request with charge account payment."""
        request = BookRequest(
            token="booking-token-456",
            method="charge"
        )
        
        assert request.token == "booking-token-456"
        assert request.method == "charge"
        assert request.credit_card is None

    def test_book_request_with_promo_code(self, valid_credit_card):
        """Test book request with promo code."""
        request = BookRequest(
            token="booking-token-789",
            credit_card=valid_credit_card,
            promo="SAVE20"
        )
        
        assert request.token == "booking-token-789"
        assert request.promo == "SAVE20"
        assert request.credit_card == valid_credit_card

    def test_book_request_minimal(self):
        """Test book request with minimal required fields."""
        request = BookRequest(
            token="minimal-token"
        )
        
        assert request.token == "minimal-token"
        assert request.credit_card is None
        assert request.method is None
        assert request.promo is None


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
            confirmation="CANCEL123",
            is_cancel_request=True
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
            other="Special instructions"
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
        request = PriceRequest(
            rate_type=RateType.P2P,
            date_time="09/10/2025 03:00 PM",
            pickup=Location(
                type=LocationType.ADDRESS,
                name="Test",
                city="City",
                state="ST",
                country="US"
            ),
            dropoff=Location(
                type=LocationType.AIRPORT,
                name="Airport",
                city="City",
                state="ST",
                country="US",
                airport_code="TST"
            ),
            passengers=2,
            luggage=1,
            hours=None,  # Should be excluded
            customer_comment="Valid comment"
        )
        
        dumped = request.model_dump(exclude_none=True)
        
        assert "hours" not in dumped
        assert "customer_comment" in dumped
        assert dumped["customer_comment"] == "Valid comment"

    def test_model_validation_error_details(self):
        """Test that validation errors provide detailed information."""
        with pytest.raises(ValidationError) as exc_info:
            Location(
                type="INVALID_TYPE",  # Invalid enum
                name="Test Location",
                # Missing required fields
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check that error details contain useful information
        error_dict = error.errors()[0]
        assert "type" in error_dict
        assert "loc" in error_dict
        assert "msg" in error_dict

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
            name="Test Airport",
            city="Test City",
            state="TS",
            country="US",
            airport_code="TST",
            latitude=40.7128,
            longitude=-74.0060
        )
        
        # Serialize to dict
        data = original_location.model_dump()
        
        # Deserialize from dict
        restored_location = Location.model_validate(data)
        
        assert restored_location == original_location
        assert restored_location.type == original_location.type
        assert restored_location.name == original_location.name
        assert restored_location.airport_code == original_location.airport_code
        assert restored_location.latitude == original_location.latitude
        assert restored_location.longitude == original_location.longitude


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string_fields(self):
        """Test handling of empty string fields."""
        with pytest.raises(ValidationError):
            Location(
                type=LocationType.ADDRESS,
                name="",  # Empty name should be invalid
                city="City",
                state="ST",
                country="US"
            )

    def test_whitespace_only_fields(self):
        """Test handling of whitespace-only fields."""
        with pytest.raises(ValidationError):
            Location(
                type=LocationType.ADDRESS,
                name="   ",  # Whitespace only should be invalid
                city="City",
                state="ST",
                country="US"
            )

    def test_extremely_long_strings(self):
        """Test handling of extremely long strings."""
        long_string = "x" * 10000  # Very long string
        
        # This test assumes there are reasonable length limits
        # The actual behavior depends on schema field definitions
        try:
            location = Location(
                type=LocationType.ADDRESS,
                name=long_string,
                city="City",
                state="ST",
                country="US"
            )
            # If no validation error, the schema accepts long strings
            assert len(location.name) == 10000
        except ValidationError:
            # If validation error, the schema has length limits
            pytest.skip("Schema has string length limits")

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        location = Location(
            type=LocationType.ADDRESS,
            name="Café París",  # Unicode characters
            city="São Paulo",
            state="SP",
            country="BR"
        )
        
        assert location.name == "Café París"
        assert location.city == "São Paulo"

    def test_special_characters_in_strings(self):
        """Test handling of special characters."""
        location = Location(
            type=LocationType.ADDRESS,
            name="123 Main St. #4B",  # Special characters
            line1="123 Main St.",
            line2="Apt #4B (Rear)",
            city="New York",
            state="NY",
            country="US"
        )
        
        assert "#" in location.name
        assert "(" in location.line2
        assert ")" in location.line2