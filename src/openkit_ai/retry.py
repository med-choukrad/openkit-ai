"""A small retry helper for transient failures in AI/API calls."""

from __future__ import annotations

import asyncio
import math
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


def _validate_retry_options(
    retry_on: tuple[type[Exception], ...],
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    jitter: float,
) -> None:
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts must be a positive integer")
    for name, value in (("base_delay", base_delay), ("max_delay", max_delay)):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"{name} must be a finite non-negative number")
    if (
        isinstance(jitter, bool)
        or not isinstance(jitter, (int, float))
        or not math.isfinite(jitter)
        or not 0 <= jitter <= 1
    ):
        raise ValueError("jitter must be a finite number between 0 and 1")
    if not isinstance(retry_on, tuple) or not retry_on or not all(
        isinstance(error_type, type) and issubclass(error_type, Exception)
        for error_type in retry_on
    ):
        raise ValueError("retry_on must be a non-empty tuple of Exception types")


def _retry_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter: float,
    random_value: Callable[[], float],
) -> float:
    delay = min(max_delay, base_delay * (2**attempt))
    if jitter:
        sample = random_value()
        if (
            isinstance(sample, bool)
            or not isinstance(sample, (int, float))
            or not math.isfinite(sample)
            or not 0 <= sample <= 1
        ):
            raise ValueError("random_value must return a finite number between 0 and 1")
        delay *= 1 - jitter + (2 * jitter * sample)
    return min(max_delay, delay)


def call_with_retry(
    operation: Callable[[], T],
    *,
    retry_on: tuple[type[Exception], ...] = (TimeoutError, ConnectionError),
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    jitter: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
    random_value: Callable[[], float] = random.random,
) -> T:
    """Run an operation, retrying selected transient exceptions.

    Delays grow exponentially and are capped by max_delay. Jitter adds a
    random spread to reduce synchronized retries. Inject sleep and
    random_value in tests. max_attempts includes the first call.
    """
    _validate_retry_options(retry_on, max_attempts, base_delay, max_delay, jitter)

    for attempt in range(max_attempts):
        try:
            return operation()
        except retry_on:
            if attempt == max_attempts - 1:
                raise
            delay = _retry_delay(attempt, base_delay, max_delay, jitter, random_value)
            sleep(delay)

    raise RuntimeError("unreachable")


async def async_call_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    retry_on: tuple[type[Exception], ...] = (TimeoutError, ConnectionError),
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    jitter: float = 0.1,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    random_value: Callable[[], float] = random.random,
) -> T:
    """Run an async operation, retrying selected transient exceptions.

    Delays grow exponentially and are capped by max_delay. Jitter adds a
    random spread to reduce synchronized retries. Inject sleep and
    random_value in tests. max_attempts includes the first call.
    """
    _validate_retry_options(retry_on, max_attempts, base_delay, max_delay, jitter)

    for attempt in range(max_attempts):
        try:
            return await operation()
        except retry_on:
            if attempt == max_attempts - 1:
                raise
            delay = _retry_delay(attempt, base_delay, max_delay, jitter, random_value)
            await sleep(delay)

    raise RuntimeError("unreachable")
