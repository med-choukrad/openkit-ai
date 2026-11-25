"""A small retry helper for transient failures in AI/API calls."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


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
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay < 0 or max_delay < 0:
        raise ValueError("delays cannot be negative")
    if not 0 <= jitter <= 1:
        raise ValueError("jitter must be between 0 and 1")
    if not retry_on or not all(
        isinstance(error_type, type) and issubclass(error_type, Exception)
        for error_type in retry_on
    ):
        raise ValueError("retry_on must contain one or more Exception types")

    for attempt in range(max_attempts):
        try:
            return operation()
        except retry_on:
            if attempt == max_attempts - 1:
                raise
            delay = min(max_delay, base_delay * (2**attempt))
            if jitter:
                delay *= 1 - jitter + (2 * jitter * random_value())
            sleep(delay)

    raise RuntimeError("unreachable")
