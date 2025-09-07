"""
Logging utilities for the Bookalimo SDK.

The SDK uses Python's standard logging module. To enable debug logging,
configure the 'bookalimo' logger or set the BOOKALIMO_LOG_LEVEL environment variable.

Example:
    import logging
    logging.getLogger('bookalimo').setLevel(logging.DEBUG)

    # Or via environment variable
    export BOOKALIMO_LOG_LEVEL=DEBUG
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Awaitable, Iterable, Mapping
from functools import wraps
from time import perf_counter
from typing import Any, Callable, TypeVar

from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def _level_from_env() -> int | None:
    """Get log level from BOOKALIMO_LOG_LEVEL environment variable."""
    lvl = os.getenv("BOOKALIMO_LOG_LEVEL")
    if not lvl:
        return None
    try:
        return int(lvl)
    except ValueError:
        try:
            return logging._nameToLevel.get(lvl.upper(), None)
        except Exception:
            return None


logger = logging.getLogger("bookalimo")

# Apply environment variable level if set, otherwise use WARNING as default
env_level = _level_from_env()
logger.setLevel(env_level if env_level is not None else logging.WARNING)

# If user set BOOKALIMO_LOG_LEVEL, they expect to see logs - add console handler
if env_level is not None:
    # Only add console handler if one doesn't already exist
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(env_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
else:
    # If no env var is set, use NullHandler (library default behavior)
    logger.addHandler(logging.NullHandler())

REDACTED = "******"


def mask_token(s: Any, *, show_prefix: int = 6, show_suffix: int = 2) -> str:
    if not isinstance(s, str) or not s:
        return REDACTED
    if len(s) <= show_prefix + show_suffix:
        return REDACTED
    return f"{s[:show_prefix]}…{s[-show_suffix:]}"


def mask_email(s: Any) -> str:
    if not isinstance(s, str) or "@" not in s:
        return REDACTED
    name, domain = s.split("@", 1)
    return f"{name[:1]}***@{domain}"


def mask_phone(s: Any) -> str:
    if not isinstance(s, str):
        return REDACTED
    digits = re.sub(r"\D", "", s)
    tail = digits[-4:] if digits else ""
    return f"***-***-{tail}" if tail else REDACTED


def mask_card_number(s: Any) -> str:
    if not isinstance(s, str) or len(s) < 4:
        return REDACTED
    return f"**** **** **** {s[-4:]}"


def _safe_str(x: Any) -> str:
    # Avoid large/complex reprs when logging
    try:
        s = str(x)
    except Exception:
        s = object.__repr__(x)
    # hard scrub for obvious long tokens
    if len(s) > 256:
        return s[:256] + "…"
    return s


def summarize_card(card: Any) -> dict[str, Any]:
    """
    Produce a tiny, safe card summary from either a mapping or an object with attributes.
    """

    def get(obj: Any, key: str) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(key)
        return getattr(obj, key, None)

    number = get(card, "number")
    exp = get(card, "expiration")
    holder_type = get(card, "holder_type")
    zip_code = get(card, "zip") or get(card, "zip_code")

    return {
        "last4": number[-4:] if isinstance(number, str) and len(number) >= 4 else None,
        "expiration": REDACTED if exp else None,
        "holder_type": str(holder_type) if holder_type is not None else None,
        "zip_present": bool(zip_code),
    }


def summarize_mapping(
    data: Mapping[str, Any], *, whitelist: Iterable[str] | None = None
) -> dict[str, Any]:
    """
    Keep only whitelisted keys; for everything else just show presence (True/False).
    Avoids logging raw contents of complex payloads.
    """
    out: dict[str, Any] = {}
    allowed = set(whitelist or [])
    for k, v in data.items():
        if k in allowed:
            out[k] = v
        else:
            out[k] = bool(v)  # presence only
    return out


def redact_param(name: str, value: Any) -> Any:
    key = name.lower()
    if key in {"password", "password_hash"}:
        return REDACTED
    if key in {"token", "authorization", "authorization_bearer", "api_key", "secret"}:
        return mask_token(value)
    if key in {"email"}:
        return mask_email(value)
    if key in {"phone"}:
        return mask_phone(value)
    if key in {"cvv", "cvc", "promo"}:
        return REDACTED
    if key in {"number", "card_number"}:
        return mask_card_number(value)
    if key in {"credit_card", "card"}:
        return summarize_card(value)
    if key in {"zip", "zipcode", "postal_code"}:
        return REDACTED
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    return _safe_str(value)


# ---- public API --------------------------------------------------------------


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        return logging.getLogger(f"bookalimo.{name}")
    return logger


# ---- decorator for async methods --------------------------------------------


def log_call(
    *,
    include_params: Iterable[str] | None = None,
    transforms: Mapping[str, Callable[[Any], Any]] | None = None,
    operation: str | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    include = set(include_params or [])
    transforms = transforms or {}

    def _decorate(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def _async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log = get_logger("wrapper")
            op = operation or fn.__name__

            debug_on = log.isEnabledFor(logging.DEBUG)
            if debug_on:
                snapshot: dict[str, Any] = {}
                for k in include:
                    val = kwargs.get(k, None)
                    if k in transforms:
                        try:
                            val = transforms[k](val)
                        except Exception:
                            val = REDACTED
                    else:
                        val = redact_param(k, val)
                    snapshot[k] = val
                start = perf_counter()
                log.debug(
                    "→ %s(%s)",
                    op,
                    ", ".join(f"{k}={snapshot[k]}" for k in snapshot),
                    extra={"operation": op},
                )

            try:
                result = await fn(*args, **kwargs)
                if debug_on:
                    dur_ms = (perf_counter() - start) * 1000.0
                    log.debug(
                        "← %s ok in %.1f ms (%s)",
                        op,
                        dur_ms,
                        type(result).__name__,
                        extra={"operation": op},
                    )
                return result
            except Exception as e:
                log.warning(
                    "%s failed: %s", op, e.__class__.__name__, extra={"operation": op}
                )
                raise

        return _async_wrapper

    return _decorate
