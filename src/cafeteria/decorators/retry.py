from __future__ import annotations

import asyncio
import functools
import inspect
import random
import time
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any
from typing import ParamSpec
from typing import TypeVar
from typing import overload

from cafeteria.datastructs.units.time import Duration

P = ParamSpec("P")
T = TypeVar("T")

__all__ = ["retry"]


def _calculate_sleep(
    attempt: int,
    backoff: float,
    factor: float,
    max_backoff: float | None,
    jitter: bool | float | tuple[float, float],
) -> float:
    """Calculate sleep time for a given retry attempt."""
    delay = backoff * (factor ** (attempt - 1))
    if max_backoff is not None:
        delay = min(delay, max_backoff)

    if jitter is True:
        delay = random.uniform(0.0, delay) if delay > 0 else 0.0
    elif isinstance(jitter, tuple) and len(jitter) == 2:
        delay = delay + random.uniform(float(jitter[0]), float(jitter[1]))
    elif isinstance(jitter, (int, float)) and not isinstance(jitter, bool):
        delay = delay + random.uniform(0.0, float(jitter))

    return max(0.0, delay)


def _should_retry(
    exc: BaseException,
    retry_on: (type[BaseException] | tuple[type[BaseException], ...] | Callable[[Any], bool]),
    dont_retry_on: type[BaseException] | tuple[type[BaseException], ...] | None,
) -> bool:
    """Determine whether an exception should trigger a retry."""
    if dont_retry_on is not None and isinstance(exc, dont_retry_on):
        return False

    if isinstance(retry_on, (type, tuple)):
        return isinstance(exc, retry_on)

    if callable(retry_on):
        if not isinstance(exc, Exception):
            return False
        return bool(retry_on(exc))

    return False


@overload
def retry(
    _func: Callable[P, Awaitable[T]],
    *,
    attempts: int = 3,
    backoff: float | int | Duration = 0.0,
    factor: float | int = 2.0,
    max_backoff: float | int | Duration | None = None,
    jitter: bool | float | tuple[float, float] = False,
    retry_on: (
        type[BaseException] | tuple[type[BaseException], ...] | Callable[[Any], bool]
    ) = Exception,
    dont_retry_on: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    on_retry: Callable[[Any, int, float], Any] | None = None,
) -> Callable[P, Awaitable[T]]: ...


@overload
def retry(
    _func: Callable[P, T],
    *,
    attempts: int = 3,
    backoff: float | int | Duration = 0.0,
    factor: float | int = 2.0,
    max_backoff: float | int | Duration | None = None,
    jitter: bool | float | tuple[float, float] = False,
    retry_on: (
        type[BaseException] | tuple[type[BaseException], ...] | Callable[[Any], bool]
    ) = Exception,
    dont_retry_on: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    on_retry: Callable[[Any, int, float], Any] | None = None,
) -> Callable[P, T]: ...


@overload
def retry(
    _func: None = None,
    *,
    attempts: int = 3,
    backoff: float | int | Duration = 0.0,
    factor: float | int = 2.0,
    max_backoff: float | int | Duration | None = None,
    jitter: bool | float | tuple[float, float] = False,
    retry_on: (
        type[BaseException] | tuple[type[BaseException], ...] | Callable[[Any], bool]
    ) = Exception,
    dont_retry_on: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    on_retry: Callable[[Any, int, float], Any] | None = None,
) -> Callable[[Callable[P, Any]], Callable[P, Any]]: ...


def retry(
    _func: Callable[P, Any] | None = None,
    *,
    attempts: int = 3,
    backoff: float | int | Duration = 0.0,
    factor: float | int = 2.0,
    max_backoff: float | int | Duration | None = None,
    jitter: bool | float | tuple[float, float] = False,
    retry_on: (
        type[BaseException] | tuple[type[BaseException], ...] | Callable[[Any], bool]
    ) = Exception,
    dont_retry_on: type[BaseException] | tuple[type[BaseException], ...] | None = None,
    on_retry: Callable[[Any, int, float], Any] | None = None,
) -> Any:
    """
    Zero-dependency retry decorator supporting both sync and async functions with exponential
    backoff, jitter, and selective exception catching.

    :param _func: Function to decorate when used as a bare decorator `@retry`.
    :param attempts: Maximum number of execution attempts (initial attempt + retries). Must be >= 1.
    :param backoff: Initial backoff delay in seconds or `Duration` before the first retry.
    :param factor: Exponential multiplier applied to backoff for each subsequent retry.
    :param max_backoff: Maximum delay cap in seconds or `Duration`.
    :param jitter: Jitter mode. `True` applies full jitter `[0, delay]`. A numeric value adds
        random offset `[0, jitter]`. A 2-tuple `(min, max)` adds random offset `[min, max]`.
    :param retry_on: Exception class, tuple of exception classes, or predicate function
        `Callable[[Exception], bool]` indicating which exceptions should trigger a retry.
    :param dont_retry_on: Exception class or tuple of exception classes to immediately re-raise
        without retrying.
    :param on_retry: Optional hook `Callable[[Exception, int, float], Any]` invoked before each
        retry with arguments `(exception, attempt_number, sleep_duration)`.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be >= 1, got {attempts}")
    if backoff < 0:
        raise ValueError(f"backoff must be non-negative, got {backoff}")
    if factor < 0:
        raise ValueError(f"factor must be non-negative, got {factor}")
    if max_backoff is not None and max_backoff < 0:
        raise ValueError(f"max_backoff must be non-negative, got {max_backoff}")

    backoff_float = float(backoff)
    factor_float = float(factor)
    max_backoff_float = float(max_backoff) if max_backoff is not None else None

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                for attempt in range(1, attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except BaseException as exc:
                        if attempt >= attempts or not _should_retry(exc, retry_on, dont_retry_on):
                            raise

                        sleep_time = _calculate_sleep(
                            attempt,
                            backoff_float,
                            factor_float,
                            max_backoff_float,
                            jitter,
                        )

                        if on_retry is not None:
                            res = on_retry(exc, attempt, sleep_time)
                            if inspect.isawaitable(res):
                                await res

                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except BaseException as exc:
                    if attempt >= attempts or not _should_retry(exc, retry_on, dont_retry_on):
                        raise

                    sleep_time = _calculate_sleep(
                        attempt,
                        backoff_float,
                        factor_float,
                        max_backoff_float,
                        jitter,
                    )

                    if on_retry is not None:
                        res = on_retry(exc, attempt, sleep_time)
                        if inspect.isawaitable(res):
                            res.close()

                    if sleep_time > 0:
                        time.sleep(sleep_time)

        return sync_wrapper

    if _func is not None:
        return decorator(_func)

    return decorator
