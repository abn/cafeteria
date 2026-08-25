from __future__ import annotations

import asyncio
import contextlib
import functools
import inspect
import math
from collections.abc import Awaitable
from collections.abc import Callable
from enum import Enum
from typing import Any
from typing import ParamSpec
from typing import TypeVar
from typing import overload

from cafeteria.datastructs.units.time import Duration
from cafeteria.logging import LoggedObject

P = ParamSpec("P")
T = TypeVar("T")

__all__ = [
    "AsyncTimer",
    "PeriodicTask",
    "PeriodicTaskState",
    "async_timer",
    "periodic_task",
]


def _is_coroutine_function(func: Any) -> bool:
    """Helper to detect coroutine functions including unwrapped/partial functions."""
    unwrapped = inspect.unwrap(func)
    if inspect.iscoroutinefunction(unwrapped):
        return True
    if isinstance(unwrapped, functools.partial):
        return _is_coroutine_function(unwrapped.func)
    return False


class PeriodicTaskState(str, Enum):
    """
    Lifecycle states of a periodic task runner.
    """

    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


class PeriodicTask(LoggedObject):
    """
    A recurring coroutine runner with monotonic drift compensation, start/stop/pause/resume
    controls, error handling hooks, and graceful cancellation integration.

    Supports direct instantiation, decorator usage (`@periodic_task` / `@PeriodicTask`),
    method binding, and asynchronous/synchronous context managers.
    """

    def __init__(
        self,
        func: Callable[..., Awaitable[Any]] | None = None,
        *,
        interval: float | int | Duration = 1.0,
        immediate: bool = False,
        autostart: bool = False,
        raise_exceptions: bool = False,
        on_error: Callable[[Exception], Any] | None = None,
        name: str | None = None,
    ) -> None:
        interval_val = float(interval)
        if math.isnan(interval_val) or interval_val <= 0:
            raise ValueError(f"interval must be a positive finite number, got {interval}")

        self._func = func
        self._interval = interval_val
        self._immediate = immediate
        self._autostart = autostart
        self._raise_exceptions = raise_exceptions
        self._on_error = on_error
        self._name = name or (getattr(func, "__name__", None) if func else None)

        self._state: PeriodicTaskState = PeriodicTaskState.STOPPED
        self._task: asyncio.Task[None] | None = None
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()
        self._iterations: int = 0
        self._last_run_at: float | None = None
        self._next_run_at: float | None = None
        self._bound_args: tuple[Any, ...] = ()
        self._bound_kwargs: dict[str, Any] = {}

        if func is not None:
            if not _is_coroutine_function(func):
                raise TypeError(
                    "PeriodicTask target function must be a coroutine function (async def)"
                )
            functools.update_wrapper(self, func)

        if self._autostart and self._func is not None:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    self.start()
            except RuntimeError:
                pass

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} name={self._name!r} "
            f"state={self._state.value} interval={self._interval} iterations={self._iterations}>"
        )

    @property
    def interval(self) -> float:
        """The interval in seconds between periodic executions."""
        return self._interval

    @property
    def immediate(self) -> bool:
        """Whether the first iteration executes immediately upon starting."""
        return self._immediate

    @property
    def state(self) -> PeriodicTaskState:
        """The current lifecycle state of the periodic runner."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Return True if the runner is active and not paused or stopped."""
        return self._state == PeriodicTaskState.RUNNING

    @property
    def is_paused(self) -> bool:
        """Return True if the runner is in a paused state."""
        return self._state == PeriodicTaskState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """Return True if the runner is stopped."""
        return self._state == PeriodicTaskState.STOPPED

    @property
    def task(self) -> asyncio.Task[None] | None:
        """The underlying asyncio.Task running the periodic loop, if active."""
        return self._task

    @property
    def iterations(self) -> int:
        """The total number of completed executions."""
        return self._iterations

    @property
    def last_run_at(self) -> float | None:
        """Monotonic timestamp of the most recent execution start."""
        return self._last_run_at

    @property
    def next_run_at(self) -> float | None:
        """Monotonic target timestamp of the next scheduled execution."""
        return self._next_run_at

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        If used as a decorator on a function, bind the function.
        If already bound, execute a single tick directly.
        """
        if self._func is None:
            if len(args) == 1 and callable(args[0]) and not kwargs:
                target_func = args[0]
                if not _is_coroutine_function(target_func):
                    raise TypeError(
                        "PeriodicTask target function must be a coroutine function (async def)"
                    )
                self._func = target_func
                self._name = self._name or getattr(target_func, "__name__", None)
                functools.update_wrapper(self, target_func)
                if self._autostart:
                    try:
                        loop = asyncio.get_running_loop()
                        if loop.is_running():
                            self.start()
                    except RuntimeError:
                        pass
                return self
            raise ValueError("PeriodicTask is unconfigured. Pass a coroutine function to decorate.")

        return self.tick(*args, **kwargs)

    def __get__(self, instance: Any, owner: type[Any] | None = None) -> PeriodicTask:
        """
        Support method decoration by binding instance to the target coroutine and caching
        the bound runner on the instance so repeated attribute accesses return the same runner.
        """
        if instance is None or self._func is None:
            return self

        name = self._name
        if name and hasattr(instance, "__dict__") and name in instance.__dict__:
            cached = instance.__dict__[name]
            if isinstance(cached, PeriodicTask):
                return cached

        func_get: Any = getattr(self._func, "__get__", None)
        bound_func: Callable[..., Awaitable[Any]] = (
            func_get(instance, owner) if callable(func_get) else self._func
        )
        bound_runner = PeriodicTask(
            bound_func,
            interval=self._interval,
            immediate=self._immediate,
            autostart=self._autostart,
            raise_exceptions=self._raise_exceptions,
            on_error=self._on_error,
            name=self._name,
        )
        if name and hasattr(instance, "__dict__"):
            instance.__dict__[name] = bound_runner
        return bound_runner

    async def tick(self, *args: Any, **kwargs: Any) -> Any:
        """
        Manually trigger and await a single execution of the target coroutine.
        """
        if self._func is None:
            raise RuntimeError("Cannot execute tick: no target function assigned.")

        call_args = args if args else self._bound_args
        call_kwargs = kwargs if kwargs else self._bound_kwargs

        loop = asyncio.get_running_loop()
        self._last_run_at = loop.time()
        res = await self._func(*call_args, **call_kwargs)
        self._iterations += 1
        return res

    def start(self, *args: Any, **kwargs: Any) -> PeriodicTask:
        """
        Start the periodic execution loop.

        :param args: Optional default positional arguments passed to the coroutine.
        :param kwargs: Optional default keyword arguments passed to the coroutine.
        :return: self
        """
        if self._func is None:
            raise RuntimeError("Cannot start: no target function assigned.")

        if args:
            self._bound_args = args
        if kwargs:
            self._bound_kwargs = kwargs

        if self._state == PeriodicTaskState.RUNNING:
            return self

        if self._state == PeriodicTaskState.PAUSED:
            self.resume()
            return self

        loop = asyncio.get_running_loop()
        next_target = loop.time()
        if not self._immediate:
            next_target += self._interval
        self._next_run_at = next_target

        self._state = PeriodicTaskState.RUNNING
        self._pause_event.set()
        task_name = f"PeriodicTask-{self._name or id(self)}"
        self._task = asyncio.create_task(self._run_loop(), name=task_name)
        return self

    def stop(self) -> None:
        """
        Stop the periodic execution loop and cancel the background task.
        """
        if self._state == PeriodicTaskState.STOPPED:
            return

        self._state = PeriodicTaskState.STOPPED
        self._next_run_at = None
        self._pause_event.set()

        if self._task is not None and not self._task.done():
            self._task.cancel()

    def pause(self) -> None:
        """
        Pause the periodic execution without destroying the task loop.
        """
        if self._state == PeriodicTaskState.RUNNING:
            self._state = PeriodicTaskState.PAUSED
            self._pause_event.clear()
            self.logger.debug("Paused periodic task %s", self._name)

    def resume(self) -> None:
        """
        Resume periodic execution from a paused state.
        """
        if self._state == PeriodicTaskState.PAUSED:
            self._state = PeriodicTaskState.RUNNING
            try:
                loop = asyncio.get_running_loop()
                self._next_run_at = loop.time() + self._interval
            except RuntimeError:
                pass
            self._pause_event.set()
            self.logger.debug("Resumed periodic task %s", self._name)

    async def _run_loop(self) -> None:
        """
        Internal loop with monotonic drift compensation and exception handling.
        """
        loop = asyncio.get_running_loop()
        next_target = self._next_run_at if self._next_run_at is not None else loop.time()

        if not self._immediate and self._next_run_at is None:
            next_target += self._interval

        self._next_run_at = next_target

        try:
            while self._state != PeriodicTaskState.STOPPED:
                # Wait for unpause if paused
                if not self._pause_event.is_set():
                    await self._pause_event.wait()
                    if self._state == PeriodicTaskState.STOPPED:
                        break
                    # Re-align target time after resuming
                    next_target = (
                        self._next_run_at
                        if self._next_run_at is not None
                        else loop.time() + self._interval
                    )
                    self._next_run_at = next_target

                # Calculate sleep duration with drift compensation
                now = loop.time()
                delay = next_target - now
                if delay > 0:
                    await asyncio.sleep(delay)

                if self._state == PeriodicTaskState.STOPPED:
                    break

                # If paused while sleeping, loop back to wait for resume
                if not self._pause_event.is_set():
                    continue

                # Execute tick
                self._last_run_at = loop.time()
                try:
                    assert self._func is not None
                    await self._func(*self._bound_args, **self._bound_kwargs)
                    self._iterations += 1
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    if self._on_error is not None:
                        try:
                            hook_res = self._on_error(exc)
                            if inspect.isawaitable(hook_res):
                                await hook_res
                        except asyncio.CancelledError:
                            raise
                        except Exception as hook_exc:
                            self.logger.exception(
                                "Error in periodic task error handler: %s", hook_exc
                            )

                    if self._raise_exceptions:
                        raise
                    self.logger.exception(
                        "Exception in periodic task execution for %s: %s", self._name, exc
                    )

                # Compute next target time avoiding backlog bursts
                now = loop.time()
                next_target += self._interval
                if next_target <= now:
                    # Overrun: advance next_target to the next future interval boundary
                    missed_intervals = int((now - next_target) // self._interval) + 1
                    next_target += missed_intervals * self._interval

                self._next_run_at = next_target

        except asyncio.CancelledError:
            if asyncio.current_task() is self._task:
                self._state = PeriodicTaskState.STOPPED
            raise
        except Exception:
            if asyncio.current_task() is self._task:
                self._state = PeriodicTaskState.STOPPED
            raise
        finally:
            if asyncio.current_task() is self._task:
                self._state = PeriodicTaskState.STOPPED

    async def __aenter__(self) -> PeriodicTask:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        task = self._task
        self.stop()
        if task is not None and not task.done():
            with contextlib.suppress(asyncio.CancelledError):
                await task

    def __enter__(self) -> PeriodicTask:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.stop()


# Alias class
AsyncTimer = PeriodicTask


@overload
def periodic_task(
    _func: Callable[P, Awaitable[T]],
    *,
    interval: float | int | Duration = 1.0,
    immediate: bool = False,
    autostart: bool = False,
    raise_exceptions: bool = False,
    on_error: Callable[[Exception], Any] | None = None,
    name: str | None = None,
) -> PeriodicTask: ...


@overload
def periodic_task(
    _func: None = None,
    *,
    interval: float | int | Duration = 1.0,
    immediate: bool = False,
    autostart: bool = False,
    raise_exceptions: bool = False,
    on_error: Callable[[Exception], Any] | None = None,
    name: str | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], PeriodicTask]: ...


def periodic_task(
    _func: Callable[P, Awaitable[T]] | None = None,
    *,
    interval: float | int | Duration = 1.0,
    immediate: bool = False,
    autostart: bool = False,
    raise_exceptions: bool = False,
    on_error: Callable[[Exception], Any] | None = None,
    name: str | None = None,
) -> Any:
    """
    Decorator to create a PeriodicTask runner around an asynchronous function.

    :param _func: The coroutine function to execute periodically.
    :param interval: Interval duration in seconds or Duration instance.
    :param immediate: If True, execute the first iteration immediately upon starting.
    :param autostart: If True and an active event loop is running, start immediately.
    :param raise_exceptions: If True, bubble up exceptions to halt the runner.
    :param on_error: Optional callback (sync or async) invoked with the Exception on failure.
    :param name: Optional name for the task.
    """
    if _func is not None:
        return PeriodicTask(
            _func,
            interval=interval,
            immediate=immediate,
            autostart=autostart,
            raise_exceptions=raise_exceptions,
            on_error=on_error,
            name=name,
        )

    def decorator(func: Callable[P, Awaitable[T]]) -> PeriodicTask:
        return PeriodicTask(
            func,
            interval=interval,
            immediate=immediate,
            autostart=autostart,
            raise_exceptions=raise_exceptions,
            on_error=on_error,
            name=name,
        )

    return decorator


# Alias decorator
async_timer = periodic_task
