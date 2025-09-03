"""
Logging configuration for bookalimo package.
Public SDK-style logging with built-in redaction helpers.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable, Mapping
from time import perf_counter
from typing import Any, Callable

logger = logging.getLogger("bookalimo")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.WARNING)

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


def enable_debug_logging(level: int | None = None) -> None:
    level = level or _level_from_env() or logging.DEBUG
    logger.setLevel(level)

    has_real_handler = any(
        not isinstance(h, logging.NullHandler) for h in logger.handlers
    )
    if not has_real_handler:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.info("bookalimo logging enabled at %s", logging.getLevelName(logger.level))


def disable_debug_logging() -> None:
    logger.setLevel(logging.WARNING)
    for handler in logger.handlers[:]:
        if not isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)


def _level_from_env() -> int | None:
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


# ---- decorator for async methods --------------------------------------------


def log_call(
    *,
    include_params: Iterable[str] | None = None,
    transforms: Mapping[str, Callable[[Any], Any]] | None = None,
    operation: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for async SDK methods.
    - DEBUG: logs start/end with sanitized params + duration
    - WARNING: logs errors (sanitized). No overhead when DEBUG is off.
    """
    include = set(include_params or [])
    transforms = transforms or {}

    def _decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        async def _async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            log = get_logger("wrapper")
            op = operation or fn.__name__

            # Fast path: if debug disabled, skip param binding/redaction entirely
            debug_on = log.isEnabledFor(logging.DEBUG)
            if debug_on:
                # Build a minimal, sanitized args snapshot
                snapshot: dict[str, Any] = {}
                # Map positional args to param names without inspect overhead by relying on kwargs only:
                # we assume call sites are using kwargs in the wrapper (they do).
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
                result = await fn(self, *args, **kwargs)
                if debug_on:
                    dur_ms = (perf_counter() - start) * 1000.0
                    # Keep result logging ultra-light
                    result_type = type(result).__name__
                    log.debug(
                        "← %s ok in %.1f ms (%s)",
                        op,
                        dur_ms,
                        result_type,
                        extra={"operation": op},
                    )
                return result
            except Exception as e:
                # WARNING with sanitized error; no param dump on failures
                log.warning(
                    "%s failed: %s", op, e.__class__.__name__, extra={"operation": op}
                )
                raise

        return _async_wrapper

    return _decorate
