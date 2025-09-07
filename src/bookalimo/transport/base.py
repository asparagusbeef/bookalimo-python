"""Base transport interface and shared utilities."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseTransport(ABC):
    """Base transport interface for sync and async implementations."""

    @abstractmethod
    def post(self, path: str, model: BaseModel, response_model: type[T]) -> T:
        """Make a POST request and return parsed response."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the transport and clean up resources."""
        ...

    def prepare_data(self, data: BaseModel) -> dict[str, Any]:
        """Prepare data for API requests by converting it to the appropriate format."""
        return data.model_dump(mode="json", exclude_none=True)


class AsyncBaseTransport(ABC):
    """Base async transport interface."""

    @abstractmethod
    async def post(self, path: str, model: BaseModel, response_model: type[T]) -> T:
        """Make a POST request and return parsed response."""
        ...

    @abstractmethod
    async def aclose(self) -> None:
        """Close the transport and clean up resources."""
        ...

    def prepare_data(self, data: BaseModel) -> dict[str, Any]:
        """Prepare data for API requests by converting it to the appropriate format."""
        return data.model_dump(mode="json", exclude_none=True)
