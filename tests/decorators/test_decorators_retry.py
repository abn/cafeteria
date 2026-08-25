from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cafeteria.datastructs import Duration
from cafeteria.datastructs import TimeUnit
from cafeteria.decorators import retry


def test_retry_sync_success_first_try() -> None:
    calls = 0

    @retry(attempts=3, backoff=0.1)
    def do_work() -> str:
        nonlocal calls
        calls += 1
        return "success"

    result = do_work()
    assert result == "success"
    assert calls == 1


@patch("time.sleep")
def test_retry_sync_success_after_retries(mock_sleep: MagicMock) -> None:
    calls = 0

    @retry(attempts=4, backoff=0.5, factor=2.0, jitter=False)
    def do_work() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError(f"fail {calls}")
        return "ok"

    result = do_work()
    assert result == "ok"
    assert calls == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(0.5)
    mock_sleep.assert_any_call(1.0)


@patch("time.sleep")
def test_retry_sync_exhausted_attempts(mock_sleep: MagicMock) -> None:
    calls = 0

    @retry(attempts=3, backoff=0.1, jitter=False)
    def always_fails() -> None:
        nonlocal calls
        calls += 1
        raise ValueError(f"failure #{calls}")

    with pytest.raises(ValueError, match="failure #3"):
        always_fails()

    assert calls == 3
    assert mock_sleep.call_count == 2


@patch("time.sleep")
def test_retry_sync_selective_exceptions(mock_sleep: MagicMock) -> None:
    calls = 0

    @retry(attempts=3, backoff=0.1, retry_on=(ConnectionError, TimeoutError))
    def fail_with_value_error() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("unhandled error")

    with pytest.raises(ValueError, match="unhandled error"):
        fail_with_value_error()

    assert calls == 1
    assert mock_sleep.call_count == 0


@patch("time.sleep")
def test_retry_sync_dont_retry_on(mock_sleep: MagicMock) -> None:
    calls = 0

    @retry(attempts=3, backoff=0.1, retry_on=Exception, dont_retry_on=(RuntimeError,))
    def fail_with_runtime_error() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("fatal")

    with pytest.raises(RuntimeError, match="fatal"):
        fail_with_runtime_error()

    assert calls == 1
    assert mock_sleep.call_count == 0


@patch("time.sleep")
def test_retry_sync_predicate_retry_on(mock_sleep: MagicMock) -> None:
    calls = 0

    def is_transient(exc: Exception) -> bool:
        return isinstance(exc, ValueError) and "transient" in str(exc)

    @retry(attempts=3, backoff=0.1, retry_on=is_transient)
    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("transient error")
        return "recovered"

    assert flaky() == "recovered"
    assert calls == 2
    assert mock_sleep.call_count == 1


@patch("time.sleep")
def test_retry_sync_predicate_rejects(mock_sleep: MagicMock) -> None:
    calls = 0

    def is_transient(exc: Exception) -> bool:
        return isinstance(exc, ValueError) and "transient" in str(exc)

    @retry(attempts=3, backoff=0.1, retry_on=is_transient)
    def fatal() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("permanent error")

    with pytest.raises(ValueError, match="permanent error"):
        fatal()

    assert calls == 1
    assert mock_sleep.call_count == 0


@patch("time.sleep")
def test_retry_predicate_with_base_exception(mock_sleep: MagicMock) -> None:
    calls = 0

    def is_transient(exc: Exception) -> bool:
        return True

    @retry(attempts=3, backoff=0.1, retry_on=is_transient)
    def raises_keyboard_interrupt() -> None:
        nonlocal calls
        calls += 1
        raise KeyboardInterrupt("stop")

    with pytest.raises(KeyboardInterrupt):
        raises_keyboard_interrupt()

    assert calls == 1
    assert mock_sleep.call_count == 0


@patch("time.sleep")
def test_retry_invalid_retry_on_type(mock_sleep: MagicMock) -> None:
    calls = 0
    invalid_retry_on: Any = "invalid_type"

    @retry(attempts=3, backoff=0.1, retry_on=invalid_retry_on)
    def failing_fn() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("err")

    with pytest.raises(ValueError, match="err"):
        failing_fn()

    assert calls == 1
    assert mock_sleep.call_count == 0


@patch("time.sleep")
def test_retry_sync_bare_decorator(mock_sleep: MagicMock) -> None:
    calls = 0

    @retry
    def bare_func() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise RuntimeError("flaky")
        return "done"

    assert bare_func() == "done"
    assert calls == 2
    assert mock_sleep.call_count == 0  # backoff default is 0.0


@patch("time.sleep")
def test_retry_sync_on_retry_callback(mock_sleep: MagicMock) -> None:
    calls = 0
    on_retry_log: list[tuple[str, int, float]] = []

    def on_retry_hook(exc: Exception, attempt: int, delay: float) -> None:
        on_retry_log.append((str(exc), attempt, delay))

    @retry(attempts=3, backoff=1.0, factor=2.0, jitter=False, on_retry=on_retry_hook)
    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError(f"attempt {calls} failed")
        return "ok"

    assert flaky() == "ok"
    assert calls == 3
    assert len(on_retry_log) == 2
    assert on_retry_log[0] == ("attempt 1 failed", 1, 1.0)
    assert on_retry_log[1] == ("attempt 2 failed", 2, 2.0)


@patch("time.sleep")
def test_retry_sync_on_retry_async_callback_closed(mock_sleep: MagicMock) -> None:
    calls = 0

    async def async_hook(exc: Exception, attempt: int, delay: float) -> None:
        pass

    @retry(attempts=2, backoff=0.1, on_retry=async_hook)
    def sync_fn() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("fail")
        return "ok"

    assert sync_fn() == "ok"
    assert calls == 2


async def test_retry_async_success_first_try() -> None:
    calls = 0

    @retry(attempts=3, backoff=0.1)
    async def do_async() -> str:
        nonlocal calls
        calls += 1
        return "async success"

    result = await do_async()
    assert result == "async success"
    assert calls == 1


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_retry_async_success_after_retries(mock_async_sleep: AsyncMock) -> None:
    calls = 0

    @retry(attempts=3, backoff=0.25, factor=2.0, jitter=False)
    async def do_async() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError(f"network down {calls}")
        return "connected"

    result = await do_async()
    assert result == "connected"
    assert calls == 3
    assert mock_async_sleep.call_count == 2
    mock_async_sleep.assert_any_await(0.25)
    mock_async_sleep.assert_any_await(0.5)


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_retry_async_exhausted_attempts(mock_async_sleep: AsyncMock) -> None:
    calls = 0

    @retry(attempts=2, backoff=0.1, jitter=False)
    async def always_fails_async() -> None:
        nonlocal calls
        calls += 1
        raise TimeoutError("timeout")

    with pytest.raises(TimeoutError, match="timeout"):
        await always_fails_async()

    assert calls == 2
    assert mock_async_sleep.call_count == 1


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_retry_async_bare_decorator(mock_async_sleep: AsyncMock) -> None:
    calls = 0

    @retry
    async def bare_async() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RuntimeError("flaky async")
        return "recovered async"

    assert await bare_async() == "recovered async"
    assert calls == 3
    assert mock_async_sleep.call_count == 0


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_retry_async_on_retry_callbacks(mock_async_sleep: AsyncMock) -> None:
    calls = 0
    async_log: list[tuple[str, int, float]] = []

    async def async_on_retry(exc: Exception, attempt: int, delay: float) -> None:
        await asyncio.sleep(0)  # coroutine work
        async_log.append((str(exc), attempt, delay))

    @retry(attempts=3, backoff=0.5, factor=3.0, jitter=False, on_retry=async_on_retry)
    async def flaky_async() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionResetError(f"reset {calls}")
        return "ok"

    assert await flaky_async() == "ok"
    assert calls == 3
    assert len(async_log) == 2
    assert async_log[0] == ("reset 1", 1, 0.5)
    assert async_log[1] == ("reset 2", 2, 1.5)


@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_retry_async_sync_on_retry_callback(mock_async_sleep: AsyncMock) -> None:
    calls = 0
    sync_log: list[tuple[str, int, float]] = []

    def sync_on_retry(exc: Exception, attempt: int, delay: float) -> None:
        sync_log.append((str(exc), attempt, delay))

    @retry(attempts=2, backoff=0.1, on_retry=sync_on_retry)
    async def flaky_async() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("transient")
        return "ok"

    assert await flaky_async() == "ok"
    assert calls == 2
    assert len(sync_log) == 1
    assert sync_log[0][0] == "transient"


def test_retry_max_backoff_clamping() -> None:
    with patch("time.sleep") as mock_sleep:
        calls = 0

        @retry(attempts=5, backoff=1.0, factor=2.0, max_backoff=2.5, jitter=False)
        def limited_backoff() -> str:
            nonlocal calls
            calls += 1
            if calls < 5:
                raise ValueError("error")
            return "done"

        assert limited_backoff() == "done"
        assert calls == 5
        # Attempt 1 -> backoff 1.0
        # Attempt 2 -> backoff 2.0
        # Attempt 3 -> min(4.0, 2.5) = 2.5
        # Attempt 4 -> min(8.0, 2.5) = 2.5
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0
        assert mock_sleep.call_args_list[2][0][0] == 2.5
        assert mock_sleep.call_args_list[3][0][0] == 2.5


def test_retry_duration_support() -> None:
    with patch("time.sleep") as mock_sleep:
        calls = 0

        @retry(
            attempts=3,
            backoff=Duration(500, TimeUnit.MILLISECONDS),
            max_backoff=Duration("1s"),
            jitter=False,
        )
        def duration_fn() -> str:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("error")
            return "done"

        assert duration_fn() == "done"
        assert mock_sleep.call_args_list[0][0][0] == 0.5
        assert mock_sleep.call_args_list[1][0][0] == 1.0


def test_retry_jitter_modes() -> None:
    with patch("time.sleep") as mock_sleep:
        # Full jitter (jitter=True) with zero delay
        @retry(attempts=2, backoff=0.0, jitter=True)
        def jitter_zero_delay_fn() -> str:
            return "zero_delay"

        assert jitter_zero_delay_fn() == "zero_delay"

        # Full jitter (jitter=True)
        @retry(attempts=2, backoff=2.0, jitter=True)
        def jitter_true_fn() -> str:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ValueError("err")
            return "ok"

        with patch("random.uniform", return_value=1.23) as mock_rand:
            calls = 0
            assert jitter_true_fn() == "ok"
            mock_rand.assert_called_once_with(0.0, 2.0)
            mock_sleep.assert_called_with(1.23)

        # Numeric jitter (jitter=0.5)
        mock_sleep.reset_mock()
        calls = 0

        @retry(attempts=2, backoff=2.0, jitter=0.5)
        def jitter_numeric_fn() -> str:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ValueError("err")
            return "ok"

        with patch("random.uniform", return_value=0.25) as mock_rand:
            calls = 0
            assert jitter_numeric_fn() == "ok"
            mock_rand.assert_called_once_with(0.0, 0.5)
            mock_sleep.assert_called_with(2.25)

        # Tuple jitter range (jitter=(0.1, 0.4))
        mock_sleep.reset_mock()
        calls = 0

        @retry(attempts=2, backoff=2.0, jitter=(0.1, 0.4))
        def jitter_tuple_fn() -> str:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ValueError("err")
            return "ok"

        with patch("random.uniform", return_value=0.3) as mock_rand:
            calls = 0
            assert jitter_tuple_fn() == "ok"
            mock_rand.assert_called_once_with(0.1, 0.4)
            mock_sleep.assert_called_with(2.3)


def test_retry_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="attempts must be >= 1"):
        retry(attempts=0)

    with pytest.raises(ValueError, match="backoff must be non-negative"):
        retry(backoff=-1.0)

    with pytest.raises(ValueError, match="factor must be non-negative"):
        retry(factor=-0.5)

    with pytest.raises(ValueError, match="max_backoff must be non-negative"):
        retry(max_backoff=-2.0)


def test_retry_preserves_function_metadata() -> None:
    @retry(attempts=2)
    def my_documented_func(x: int, y: str = "default") -> str:
        """Sample docstring."""
        return f"{x}:{y}"

    assert my_documented_func.__name__ == "my_documented_func"
    assert my_documented_func.__doc__ == "Sample docstring."
    assert my_documented_func(42, y="test") == "42:test"

    @retry(attempts=2)
    async def my_documented_async_func(x: int) -> int:
        """Async sample docstring."""
        return x * 2

    assert my_documented_async_func.__name__ == "my_documented_async_func"
    assert my_documented_async_func.__doc__ == "Async sample docstring."
