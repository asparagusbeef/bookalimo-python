"""Configuration defaults for the Bookalimo SDK."""

from ._version import __version__

# Default API configuration
DEFAULT_BASE_URL = "https://www.bookalimo.com/web/api"
DEFAULT_TIMEOUT = 5.0
DEFAULT_USER_AGENT = f"bookalimo-python/{__version__}"

# Default retry configuration
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 0.3
DEFAULT_STATUS_FORCELIST = (500, 502, 503, 504)

# Default timeouts (can be dict for httpx.Timeout)
DEFAULT_TIMEOUTS = DEFAULT_TIMEOUT
