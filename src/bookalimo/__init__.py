"""
Book-A-Limo API Wrapper Package.
Provides a clean, typed interface to the Book-A-Limo API.
"""

import importlib.metadata

from ._logging import disable_debug_logging, enable_debug_logging
from .wrapper import (
    BookALimo,
    create_address_location,
    create_airport_location,
    create_credentials,
    create_credit_card,
    create_passenger,
    create_stop,
)

__all__ = [
    "BookALimo",
    "create_credentials",
    "create_address_location",
    "create_airport_location",
    "create_stop",
    "create_passenger",
    "create_credit_card",
    "enable_debug_logging",
    "disable_debug_logging",
]

__version__ = importlib.metadata.version(__package__ or __name__)
