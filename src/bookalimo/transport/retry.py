"""Retry logic and backoff utilities."""

import asyncio
import random
from collections.abc import Awaitable
from typing import Callable, TypeVar, Union

import httpx

from ..config import DEFAULT_STATUS_FORCELIST

T = TypeVar("T")


def should_retry_status(
    status_code: int, status_forcelist: tuple[int, ...] = DEFAULT_STATUS_FORCELIST
) -> bool:
    """Check if a status code should trigger a retry."""
    return status_code in status_forcelist


def should_retry_exception(exc: Exception) -> bool:
    """Check if an exception should trigger a retry."""
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ConnectError,
            ConnectionError,
        ),
    )


def calculate_backoff(attempt: int, base_backoff: float) -> float:
    """Calculate exponential backoff with jitter."""
    # Exponential backoff: base * (2 ^ attempt)
    backoff = base_backoff * (2**attempt)
    # Add jitter: ±25% randomization
    jitter = backoff * 0.25 * (random.random() * 2 - 1)  # nosec B311: non-crypto jitter
    return float(max(0.1, backoff + jitter))  # Minimum 100ms


async def async_retry(
    func: Callable[[], Awaitable[T]],
    retries: int,
    backoff: float,
    should_retry: Callable[[Exception], bool],
) -> T:
    """Retry an async function with exponential backoff."""
    attempt = 0
    last_exc: Union[Exception, None] = None

    while attempt <= retries:
        try:
            return await func()
        except Exception as e:
            last_exc = e
            if attempt >= retries or not should_retry(e):
                break

            wait_time = calculate_backoff(attempt, backoff)
            await asyncio.sleep(wait_time)
            attempt += 1

    if last_exc is not None:
        raise last_exc
    else:
        raise RuntimeError("Last exception is None")


def sync_retry(
    func: Callable[[], T],
    retries: int,
    backoff: float,
    should_retry: Callable[[Exception], bool],
) -> T:
    """Retry a sync function with exponential backoff."""
    import time

    attempt = 0
    last_exc: Union[Exception, None] = None

    while attempt <= retries:
        try:
            return func()
        except Exception as e:
            last_exc = e
            if attempt >= retries or not should_retry(e):
                break

            wait_time = calculate_backoff(attempt, backoff)
            time.sleep(wait_time)
            attempt += 1

    # Re-raise the last exception
    if last_exc is not None:
        raise last_exc
    else:
        raise RuntimeError("Last exception is None")
    raise last_exc
