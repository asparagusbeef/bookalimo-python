"""Exception classes for the Bookalimo SDK."""

from typing import Any, Literal, Optional

from pydantic import ValidationError
from pydantic_core import ErrorDetails, InitErrorDetails


class BookalimoError(Exception): ...


class BookalimoValidationError(BookalimoError):
    """Validation error for input data that wraps Pydantic ValidationError."""

    def __init__(
        self, message: str, validation_error: Optional[ValidationError] = None
    ):
        """Initialize validation error with message and optional Pydantic ValidationError."""
        super().__init__(message)
        self._validation_error = validation_error
        self._message = message

    @property
    def message(self) -> str:
        """Get the error message."""
        return self._message

    def errors(self, **kwargs: Any) -> list[ErrorDetails]:
        """Get validation errors if available."""
        if self._validation_error:
            return self._validation_error.errors(**kwargs)
        return []

    def error_count(self) -> int:
        """Get error count."""
        if self._validation_error:
            return self._validation_error.error_count()
        return 1

    @property
    def title(self) -> str:
        """Get validation error title."""
        if self._validation_error:
            return self._validation_error.title
        return "BookalimoValidationError"

    def json(self, **kwargs: Any) -> str:
        """Get errors as JSON string."""
        if self._validation_error:
            return self._validation_error.json(**kwargs)
        import json

        return json.dumps([{"type": "error", "msg": self._message, "loc": []}])

    @classmethod
    def from_exception_data(
        cls,
        title: str,
        line_errors: list[InitErrorDetails],
        input_type: Literal["python", "json"] = "python",
        hide_input: bool = False,
    ) -> "BookalimoValidationError":
        """Create validation error from Pydantic error details."""
        # Create a proper ValidationError
        validation_error = ValidationError.from_exception_data(
            title, line_errors, input_type, hide_input
        )
        return cls(f"Validation error in {title}", validation_error)

    @classmethod
    def from_validation_error(
        cls, validation_error: ValidationError, message: Optional[str] = None
    ) -> "BookalimoValidationError":
        """Create BookalimoValidationError from an existing ValidationError."""
        if message is None:
            message = f"Validation error: {validation_error}"
        return cls(message, validation_error)


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
        if self.payload and isinstance(self.payload, dict) and "error" in self.payload:
            error_msg = self.payload["error"]
            if self.status_code:
                return f"{base}: {error_msg} (status_code={self.status_code})"
            else:
                return f"{base}: {error_msg}"
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
