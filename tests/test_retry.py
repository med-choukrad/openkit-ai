import pytest

from openkit_ai import call_with_retry


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
