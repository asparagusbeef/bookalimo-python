"""Exception classes for the Bookalimo SDK."""

from typing import Any, Literal, Optional

from pydantic import ValidationError
from pydantic_core import InitErrorDetails


# Clean error hierarchy for the SDK
class BookalimoError(Exception): ...


class BookalimoValidationError(BookalimoError, ValidationError):
    """Validation error for input data."""

    @classmethod
    def from_exception_data(
        cls,
        title: str,
        line_errors: list[InitErrorDetails],
        input_type: Literal["python", "json"] = "python",
        hide_input: bool = False,
    ) -> "BookalimoValidationError":
        """Create validation error from Pydantic error details."""
        # Create a ValidationError and then wrap it
        try:
            # This will raise ValidationError with the line_errors
            ValidationError.from_exception_data(title, line_errors)
        except ValidationError as e:
            # Create our custom error that inherits from both
            instance = cls.__new__(cls)
            ValidationError.__init__(instance, e.errors(), getattr(e, "model", None))
            BookalimoError.__init__(instance, f"Validation error in {title}")
            return instance

        # Fallback if ValidationError.from_exception_data doesn't raise
        return cls(f"Validation error in {title}")


class BookalimoRequestError(BookalimoError): ...


class BookalimoConnectionError(BookalimoError): ...


class BookalimoHTTPError(BookalimoError):
    """HTTP-related errors (4xx, 5xx responses)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} (status_code={self.status_code})" if self.status_code else base


class BookalimoTimeout(BookalimoHTTPError):
    """Request timeout errors."""

    def __init__(self, message: str = "Request timeout", **kwargs: Any):
        super().__init__(message, status_code=408, **kwargs)
        self.message = message
        self.status_code = 408
        self.payload = kwargs.get("payload", None)


class DuplicateCredentialsWarning(UserWarning): ...


class MissingCredentialsWarning(UserWarning): ...
