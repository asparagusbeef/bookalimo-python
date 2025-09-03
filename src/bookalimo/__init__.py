"""
Book-A-Limo API Wrapper Package.
Provides a clean, typed interface to the Book-A-Limo API.
"""

import importlib.metadata

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
]

__version__ = importlib.metadata.version(__package__ or __name__)
