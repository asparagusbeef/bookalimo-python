"""Version information for the bookalimo package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bookalimo")
except PackageNotFoundError:
    # Development/editable install fallback
    __version__ = "0.0.0"
