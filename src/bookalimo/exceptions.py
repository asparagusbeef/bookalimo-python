from typing import Any, Optional


class BookALimoError(Exception):
    """Base exception for Book-A-Limo API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
