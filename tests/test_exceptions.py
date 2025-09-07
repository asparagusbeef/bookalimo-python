"""Tests for custom exception classes and error handling."""

from pydantic import ValidationError
from pydantic_core import InitErrorDetails
from typing_extensions import Never

from bookalimo.exceptions import (
    BookalimoConnectionError,
    BookalimoError,
    BookalimoHTTPError,
    BookalimoRequestError,
    BookalimoTimeout,
    BookalimoValidationError,
    DuplicateCredentialsWarning,
    MissingCredentialsWarning,
)


class TestBookalimoError:
    """Tests for base BookalimoError class."""

    def test_basic_error(self):
        """Test basic error creation and inheritance."""
        error = BookalimoError("Something went wrong")

        assert isinstance(error, Exception)
        assert isinstance(error, BookalimoError)
        assert str(error) == "Something went wrong"

    def test_error_with_no_message(self):
        """Test error with no message."""
        error = BookalimoError()

        assert isinstance(error, BookalimoError)
        # Should not raise when converting to string
        str(error)

    def test_error_inheritance(self):
        """Test that subclasses inherit from BookalimoError."""
        http_error = BookalimoHTTPError("HTTP error")
        timeout_error = BookalimoTimeout("Timeout error")

        assert isinstance(http_error, BookalimoError)
        assert isinstance(timeout_error, BookalimoError)
        assert isinstance(timeout_error, BookalimoHTTPError)  # Multiple inheritance


class TestBookalimoHTTPError:
    """Tests for BookalimoHTTPError class."""

    def test_basic_http_error(self):
        """Test basic HTTP error creation."""
        error = BookalimoHTTPError("Bad Request", status_code=400)

        assert isinstance(error, BookalimoHTTPError)
        assert isinstance(error, BookalimoError)
        assert error.message == "Bad Request"
        assert error.status_code == 400
        assert error.payload is None

    def test_http_error_with_payload(self):
        """Test HTTP error with payload data."""
        payload = {"error": "Invalid request", "code": "INVALID_REQUEST"}
        error = BookalimoHTTPError("Bad Request", status_code=400, payload=payload)

        assert error.payload == payload
        assert error.status_code == 400

    def test_http_error_without_status_code(self):
        """Test HTTP error without status code."""
        error = BookalimoHTTPError("General HTTP error")

        assert error.message == "General HTTP error"
        assert error.status_code is None
        assert error.payload is None

    def test_http_error_string_representation(self):
        """Test string representation of HTTP error."""
        # With status code
        error_with_code = BookalimoHTTPError("Bad Request", status_code=400)
        assert "status_code=400" in str(error_with_code)
        assert "Bad Request" in str(error_with_code)

        # Without status code
        error_without_code = BookalimoHTTPError("General error")
        assert "status_code=" not in str(error_without_code)
        assert "General error" in str(error_without_code)

    def test_http_error_attributes(self):
        """Test that all attributes are properly set."""
        payload = {"details": "More info"}
        error = BookalimoHTTPError("Server Error", status_code=500, payload=payload)

        assert hasattr(error, "message")
        assert hasattr(error, "status_code")
        assert hasattr(error, "payload")
        assert error.message == "Server Error"
        assert error.status_code == 500
        assert error.payload == payload


class TestBookalimoTimeout:
    """Tests for BookalimoTimeout class."""

    def test_default_timeout_error(self):
        """Test default timeout error."""
        error = BookalimoTimeout()

        assert isinstance(error, BookalimoTimeout)
        assert isinstance(error, BookalimoHTTPError)
        assert isinstance(error, BookalimoError)
        assert error.message == "Request timeout"
        assert error.status_code == 408

    def test_custom_timeout_error(self):
        """Test timeout error with custom message."""
        error = BookalimoTimeout("Connection timed out after 30 seconds")

        assert error.message == "Connection timed out after 30 seconds"
        assert error.status_code == 408

    def test_timeout_error_with_payload(self):
        """Test timeout error with additional payload."""
        payload = {"timeout_duration": 30, "endpoint": "/api/booking"}
        error = BookalimoTimeout("Custom timeout", payload=payload)

        assert error.message == "Custom timeout"
        assert error.status_code == 408
        assert error.payload == payload

    def test_timeout_error_inheritance(self):
        """Test timeout error inheritance chain."""
        error = BookalimoTimeout()

        # Should be instance of all parent classes
        assert isinstance(error, BookalimoTimeout)
        assert isinstance(error, BookalimoHTTPError)
        assert isinstance(error, BookalimoError)
        assert isinstance(error, Exception)

    def test_timeout_error_string_representation(self):
        """Test string representation includes status code."""
        error = BookalimoTimeout("Network timeout")
        error_str = str(error)

        assert "Network timeout" in error_str
        assert "status_code=408" in error_str


class TestBookalimoValidationError:
    """Tests for BookalimoValidationError class."""

    def test_basic_validation_error(self):
        """Test basic validation error creation."""
        error = BookalimoValidationError("Validation failed")

        assert isinstance(error, BookalimoValidationError)
        assert isinstance(error, BookalimoError)
        # Test that it provides ValidationError-like interface
        assert hasattr(error, "errors")
        assert callable(error.errors)
        assert "Validation failed" in str(error)

    def test_validation_error_from_exception_data(self):
        """Test creating validation error from Pydantic error details."""
        error_details: list[InitErrorDetails] = [
            InitErrorDetails(
                type="missing",
                loc=("field1",),
                input={},
                ctx={},
            ),
            InitErrorDetails(
                type="string_type",
                loc=("field2",),
                input=123,
                ctx={},
            ),
        ]

        error = BookalimoValidationError.from_exception_data("TestModel", error_details)

        assert isinstance(error, BookalimoValidationError)
        assert isinstance(error, BookalimoError)
        # Test that it wraps ValidationError functionality
        assert hasattr(error, "errors")
        assert len(error.errors()) == 2  # Should have the 2 errors we created
        assert "TestModel" in str(error) or "validation error" in str(error).lower()

    def test_validation_error_preserves_pydantic_functionality(self):
        """Test that validation error preserves Pydantic ValidationError functionality."""
        # Create a simple validation error to test the interface
        try:
            from pydantic import BaseModel

            class TestModel(BaseModel):
                required_field: str

            # This should raise ValidationError
            TestModel()  # type: ignore
        except ValidationError:
            # Wrap it in our custom exception
            custom_error = BookalimoValidationError("Custom validation error")

            # Should have ValidationError methods/attributes
            assert hasattr(custom_error, "errors")
            # The custom error should be callable like ValidationError
            assert callable(custom_error.errors)


class TestOtherExceptions:
    """Tests for other exception classes."""

    def test_bookalimo_request_error(self):
        """Test BookalimoRequestError."""
        error = BookalimoRequestError("Invalid request parameters")

        assert isinstance(error, BookalimoRequestError)
        assert isinstance(error, BookalimoError)
        assert str(error) == "Invalid request parameters"

    def test_bookalimo_connection_error(self):
        """Test BookalimoConnectionError."""
        error = BookalimoConnectionError("Failed to connect to API")

        assert isinstance(error, BookalimoConnectionError)
        assert isinstance(error, BookalimoError)
        assert str(error) == "Failed to connect to API"

    def test_duplicate_credentials_warning(self):
        """Test DuplicateCredentialsWarning."""
        warning = DuplicateCredentialsWarning("Credentials provided in both places")

        assert isinstance(warning, DuplicateCredentialsWarning)
        assert isinstance(warning, UserWarning)
        assert str(warning) == "Credentials provided in both places"

    def test_missing_credentials_warning(self):
        """Test MissingCredentialsWarning."""
        warning = MissingCredentialsWarning("No credentials provided")

        assert isinstance(warning, MissingCredentialsWarning)
        assert isinstance(warning, UserWarning)
        assert str(warning) == "No credentials provided"


class TestExceptionHandling:
    """Tests for exception handling scenarios."""

    def test_exception_chaining(self):
        """Test exception chaining with raise from."""
        original_error = ValueError("Original problem")

        try:
            raise BookalimoError("Wrapper error") from original_error
        except BookalimoError as e:
            assert e.__cause__ is original_error
            assert isinstance(e.__cause__, ValueError)

    def test_exception_context(self):
        """Test exception context handling."""
        try:
            try:
                raise ValueError("First error")
            except ValueError as ve:
                raise BookalimoHTTPError("Second error", status_code=500) from ve
        except BookalimoHTTPError as e:
            assert e.__context__ is not None
            assert isinstance(e.__context__, ValueError)

    def test_multiple_exception_types(self):
        """Test handling multiple exception types."""
        exceptions = [
            BookalimoError("Base error"),
            BookalimoHTTPError("HTTP error", status_code=400),
            BookalimoTimeout("Timeout error"),
            BookalimoRequestError("Request error"),
            BookalimoConnectionError("Connection error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, BookalimoError)
            assert isinstance(exc, Exception)
            assert str(exc)  # Should be convertible to string

    def test_exception_with_complex_data(self):
        """Test exceptions with complex data structures."""
        complex_payload = {
            "errors": [
                {"field": "name", "message": "Required field missing"},
                {"field": "email", "message": "Invalid format"},
            ],
            "metadata": {
                "request_id": "req_12345",
                "timestamp": "2024-01-01T12:00:00Z",
            },
            "nested": {"deep": {"value": [1, 2, 3, {"key": "value"}]}},
        }

        error = BookalimoHTTPError(
            "Complex validation failed", status_code=422, payload=complex_payload
        )

        assert error.payload == complex_payload
        assert error.payload is not None
        assert error.payload["errors"][0]["field"] == "name"
        assert error.payload["metadata"]["request_id"] == "req_12345"
        assert error.payload["nested"]["deep"]["value"][3]["key"] == "value"

    def test_exception_serialization(self):
        """Test that exceptions can be pickled/unpickled (serialized)."""
        import pickle

        error = BookalimoHTTPError(
            "Serialization test", status_code=500, payload={"test": "data"}
        )

        # Should be able to pickle and unpickle
        pickled = pickle.dumps(error)
        unpickled = pickle.loads(pickled)

        assert isinstance(unpickled, BookalimoHTTPError)
        assert unpickled.message == error.message
        assert unpickled.status_code == error.status_code
        assert unpickled.payload == error.payload

    def test_exception_equality(self):
        """Test exception equality comparison."""
        error1 = BookalimoHTTPError("Same message", status_code=400)
        error2 = BookalimoHTTPError("Same message", status_code=400)
        error3 = BookalimoHTTPError("Different message", status_code=400)
        error4 = BookalimoHTTPError("Same message", status_code=500)

        # Note: Exception equality is based on identity by default,
        # not content, so these should not be equal unless explicitly implemented
        assert error1 is not error2
        assert error1 is not error3
        assert error1 is not error4

        # But they should have the same string representation
        assert str(error1) == str(error2)
        assert str(error1) != str(error3)
        assert str(error1) != str(error4)

    def test_exception_with_none_values(self):
        """Test exceptions with None values."""
        error = BookalimoHTTPError(
            "",  # Empty message
            status_code=None,
            payload=None,
        )

        assert error.message == ""
        assert error.status_code is None
        assert error.payload is None

        # Should not crash when converting to string
        error_str = str(error)
        assert isinstance(error_str, str)

    def test_warning_classes_inheritance(self):
        """Test that warning classes inherit properly from UserWarning."""
        warnings = [
            DuplicateCredentialsWarning("Test duplicate warning"),
            MissingCredentialsWarning("Test missing warning"),
        ]

        for warning in warnings:
            assert isinstance(warning, UserWarning)
            assert isinstance(warning, Warning)
            assert str(warning)  # Should be convertible to string

    def test_exception_traceback_preservation(self):
        """Test that exception tracebacks are preserved."""

        def raise_original() -> Never:
            raise ValueError("Original error")

        def raise_wrapper() -> Never:
            try:
                raise_original()
            except ValueError as e:
                raise BookalimoError("Wrapper error") from e

        try:
            raise_wrapper()
        except BookalimoError as e:
            # Should have traceback information
            assert e.__traceback__ is not None
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"
