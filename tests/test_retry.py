import asyncio

import pytest

from openkit_ai import async_call_with_retry, call_with_retry


def test_returns_first_success_without_sleep():
    sleeps = []
    result = call_with_retry(lambda: "ok", sleep=sleeps.append)
    assert result == "ok"
    assert sleeps == []


def test_retries_transient_error_then_succeeds():
    calls = 0
    sleeps = []

    def operation():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError("temporary")
        return "done"

    result = call_with_retry(operation, base_delay=0.25, jitter=0, sleep=sleeps.append)
    assert result == "done"
    assert calls == 3
    assert sleeps == [0.25, 0.5]


def test_does_not_retry_unlisted_exception():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise ValueError("not transient")

    with pytest.raises(ValueError):
        call_with_retry(operation, sleep=lambda _: None)
    assert calls == 1


def test_reraises_after_last_attempt():
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise ConnectionError("offline")

    with pytest.raises(ConnectionError):
        call_with_retry(operation, max_attempts=2, sleep=lambda _: None)
    assert calls == 2


def test_validates_attempt_count():
    with pytest.raises(ValueError):
        call_with_retry(lambda: None, max_attempts=0)


def test_async_returns_first_success_without_sleep():
    async def scenario():
        sleeps = []

        async def operation():
            return "ok"

        async def fake_sleep(delay):
            sleeps.append(delay)

        result = await async_call_with_retry(operation, sleep=fake_sleep)
        assert result == "ok"
        assert sleeps == []

    asyncio.run(scenario())


def test_async_retries_transient_error_then_succeeds():
    async def scenario():
        calls = 0
        sleeps = []

        async def operation():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise TimeoutError("temporary")
            return "done"

        async def fake_sleep(delay):
            sleeps.append(delay)

        result = await async_call_with_retry(
            operation, base_delay=0.25, jitter=0, sleep=fake_sleep
        )
        assert result == "done"
        assert calls == 3
        assert sleeps == [0.25, 0.5]

    asyncio.run(scenario())


def test_async_does_not_retry_unlisted_exception():
    async def scenario():
        calls = 0

        async def operation():
            nonlocal calls
            calls += 1
            raise ValueError("not transient")

        with pytest.raises(ValueError):
            await async_call_with_retry(operation, sleep=lambda _: asyncio.sleep(0))
        assert calls == 1

    asyncio.run(scenario())


def test_async_reraises_after_last_attempt():
    async def scenario():
        calls = 0

        async def operation():
            nonlocal calls
            calls += 1
            raise ConnectionError("offline")

        async def fake_sleep(_):
            return None

        with pytest.raises(ConnectionError):
            await async_call_with_retry(
                operation, max_attempts=2, sleep=fake_sleep
            )
        assert calls == 2

    asyncio.run(scenario())


def test_async_validates_attempt_count():
    async def scenario():
        async def operation():
            return None

        with pytest.raises(ValueError):
            await async_call_with_retry(operation, max_attempts=0)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "options",
    [
        {"max_attempts": True},
        {"max_attempts": 1.5},
        {"base_delay": True},
        {"base_delay": float("nan")},
        {"max_delay": float("inf")},
        {"jitter": True},
        {"jitter": float("nan")},
        {"retry_on": []},
        {"retry_on": (ValueError, 1)},
        {"retry_on": (BaseException,)},
    ],
)
def test_rejects_invalid_retry_options(options):
    with pytest.raises(ValueError):
        call_with_retry(lambda: "ok", **options)


@pytest.mark.parametrize(
    "options",
    [
        {"max_attempts": True},
        {"max_attempts": 1.5},
        {"base_delay": True},
        {"base_delay": float("nan")},
        {"max_delay": float("inf")},
        {"jitter": True},
        {"jitter": float("nan")},
        {"retry_on": []},
        {"retry_on": (ValueError, 1)},
        {"retry_on": (BaseException,)},
    ],
)
def test_async_rejects_invalid_retry_options(options):
    async def scenario():
        async def operation():
            return "ok"

        with pytest.raises(ValueError):
            await async_call_with_retry(operation, **options)

    asyncio.run(scenario())
