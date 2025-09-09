"""
Transport abstractions for Google Places clients.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Type, TypeVar

from google.api_core.client_options import ClientOptions
from google.maps.places_v1 import PlacesAsyncClient, PlacesClient

T = TypeVar("T", PlacesClient, PlacesAsyncClient)


def _get_places_client(
    api_key: str,
    client: Optional[T],
    client_type: Type[T],
) -> T:
    """Create client options with API key - shared logic."""
    return client or client_type(client_options=ClientOptions(api_key=api_key))


class SyncPlacesTransport(Protocol):
    """Protocol for synchronous Places API transport."""

    def autocomplete_places(self, *, request: dict[str, Any], **kwargs: Any) -> Any: ...

    def search_text(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any: ...

    def get_place(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any: ...

    def close(self) -> None: ...


class AsyncPlacesTransport(Protocol):
    """Protocol for asynchronous Places API transport."""

    async def autocomplete_places(
        self, *, request: dict[str, Any], **kwargs: Any
    ) -> Any: ...

    async def search_text(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any: ...

    async def get_place(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any: ...

    async def close(self) -> None: ...


class GoogleSyncTransport:
    """Synchronous transport implementation for Google Places API."""

    def __init__(self, api_key: str, client: Optional[PlacesClient] = None) -> None:
        self.client = _get_places_client(api_key, client, PlacesClient)

    def autocomplete_places(self, *, request: dict[str, Any], **kwargs: Any) -> Any:
        return self.client.autocomplete_places(request=request, **kwargs)

    def search_text(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any:
        return self.client.search_text(request=request, metadata=metadata)

    def get_place(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any:
        return self.client.get_place(request=request, metadata=metadata)

    def close(self) -> None:
        self.client.transport.close()


class GoogleAsyncTransport:
    """Asynchronous transport implementation for Google Places API."""

    def __init__(
        self, api_key: str, client: Optional[PlacesAsyncClient] = None
    ) -> None:
        self.client = _get_places_client(api_key, client, PlacesAsyncClient)

    async def autocomplete_places(
        self, *, request: dict[str, Any], **kwargs: Any
    ) -> Any:
        return await self.client.autocomplete_places(request=request, **kwargs)

    async def search_text(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any:
        return await self.client.search_text(request=request, metadata=metadata)

    async def get_place(
        self, *, request: dict[str, Any], metadata: tuple[tuple[str, str], ...]
    ) -> Any:
        return await self.client.get_place(request=request, metadata=metadata)

    async def close(self) -> None:
        await self.client.transport.close()
