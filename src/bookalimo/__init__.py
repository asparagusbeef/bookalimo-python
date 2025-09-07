"""
Bookalimo SDK - Python client for the Book-A-Limo API.

Provides clean, typed interfaces for booking transportation services.
"""

from ._version import __version__
from .client import AsyncBookalimo, Bookalimo
from .exceptions import (
    BookalimoError,
    BookalimoHTTPError,
    BookalimoTimeout,
    BookalimoValidationError,
)

__all__ = [
    "Bookalimo",
    "AsyncBookalimo",
    "BookalimoError",
    "BookalimoHTTPError",
    "BookalimoTimeout",
    "BookalimoValidationError",
    "__version__",
]
