from __future__ import annotations

import asyncio
import functools
from typing import Any
from typing import cast

import pytest

from cafeteria.asyncio import AsyncTimer
from cafeteria.asyncio import PeriodicTask
from cafeteria.asyncio import PeriodicTaskState
from cafeteria.asyncio import async_timer
from cafeteria.asyncio import cancel_all_tasks
from cafeteria.asyncio import periodic_task
from cafeteria.datastructs.units.time import Duration
from cafeteria.datastructs.units.time import TimeUnit


def test_periodic_task_invalid_interval() -> None:
    async def dummy() -> None:
        pass

    with pytest.raises(ValueError, match="positive finite number"):
        PeriodicTask(dummy, interval=0)

    with pytest.raises(ValueError, match="positive finite number"):
        PeriodicTask(dummy, interval=-1.5)


def test_periodic_task_invalid_target() -> None:
    def sync_dummy() -> None:
        pass

    with pytest.raises(TypeError, match="must be a coroutine function"):
        periodic_task(cast(Any, sync_dummy))


def test_periodic_task_unconfigured_call() -> None:
    task = PeriodicTask()
    with pytest.raises(ValueError, match="PeriodicTask is unconfigured"):
        task(1, 2)


@pytest.mark.asyncio
async def test_periodic_task_basic_execution() -> None:
    count = 0

    @periodic_task(interval=0.02, immediate=True)
    async def sample_job() -> None:
        nonlocal count
        count += 1

    assert sample_job.state == PeriodicTaskState.STOPPED
    assert sample_job.is_stopped
    assert not sample_job.is_running
    assert not sample_job.is_paused

    sample_job.start()
    assert sample_job.is_running
    assert not sample_job.is_stopped

    await asyncio.sleep(0.065)
    sample_job.stop()

    assert sample_job.is_stopped
    assert not sample_job.is_running
    assert count >= 3
    assert sample_job.iterations == count


@pytest.mark.asyncio
async def test_periodic_task_immediate_false() -> None:
    count = 0

    @PeriodicTask(interval=0.05, immediate=False)
    async def delayed_job() -> None:
        nonlocal count
        count += 1

    delayed_job.start()
    # Right after start, should not have run yet because immediate=False
    await asyncio.sleep(0.01)
    assert count == 0

    await asyncio.sleep(0.06)
    delayed_job.stop()
    assert count >= 1


@pytest.mark.asyncio
async def test_periodic_task_drift_compensation() -> None:
    interval = 0.04
    work_duration = 0.015
    ticks: list[float] = []

    @periodic_task(interval=interval, immediate=True)
    async def measured_job() -> None:
        ticks.append(asyncio.get_running_loop().time())
        await asyncio.sleep(work_duration)

    start_time = asyncio.get_running_loop().time()
    measured_job.start()

    # Run for 4 intervals
    await asyncio.sleep(interval * 4 + 0.01)
    measured_job.stop()

    total_time = asyncio.get_running_loop().time() - start_time
    assert len(ticks) >= 4

    # Without drift compensation, 4 ticks with work would take ~4 * (0.04 + 0.015) = 0.22s
    # With drift compensation, 4 ticks should take ~4 * 0.04 = 0.16s
    expected_drifting_time = 4 * (interval + work_duration)
    assert total_time < expected_drifting_time


@pytest.mark.asyncio
async def test_periodic_task_overrun_handling() -> None:
    ticks: list[float] = []

    @periodic_task(interval=0.03, immediate=True)
    async def slow_job() -> None:
        ticks.append(asyncio.get_running_loop().time())
        if len(ticks) == 1:
            # First tick takes 2.5 intervals
            await asyncio.sleep(0.075)

    slow_job.start()
    await asyncio.sleep(0.12)
    slow_job.stop()

    # Should not burst executions immediately back to back to catch up missed slots
    assert len(ticks) >= 2


@pytest.mark.asyncio
async def test_periodic_task_pause_and_resume() -> None:
    count = 0

    @periodic_task(interval=0.02, immediate=True)
    async def pausable_job() -> None:
        nonlocal count
        count += 1

    pausable_job.start()
    await asyncio.sleep(0.03)
    assert count >= 1

    pausable_job.pause()
    assert pausable_job.is_paused
    assert not pausable_job.is_running
    assert not pausable_job.is_stopped

    count_at_pause = count
    # Sleep while paused and verify count does not increase
    await asyncio.sleep(0.05)
    assert count == count_at_pause

    pausable_job.resume()
    assert pausable_job.is_running
    assert not pausable_job.is_paused

    await asyncio.sleep(0.05)
    pausable_job.stop()
    assert count > count_at_pause


@pytest.mark.asyncio
async def test_periodic_task_autostart() -> None:
    count = 0

    @periodic_task(interval=0.02, immediate=True, autostart=True)
    async def auto_job() -> None:
        nonlocal count
        count += 1

    assert auto_job.is_running
    await asyncio.sleep(0.05)
    auto_job.stop()
    assert count >= 2


@pytest.mark.asyncio
async def test_periodic_task_manual_tick_and_args() -> None:
    results: list[str] = []

    @periodic_task(interval=1.0)
    async def greet(name: str, greeting: str = "Hello") -> str:
        msg = f"{greeting}, {name}!"
        results.append(msg)
        return msg

    res = await greet.tick("Alice", greeting="Hi")
    assert res == "Hi, Alice!"
    assert results == ["Hi, Alice!"]
    assert greet.iterations == 1
    assert greet.last_run_at is not None

    res2 = await greet("Bob")
    assert res2 == "Hello, Bob!"
    assert greet.iterations == 2


@pytest.mark.asyncio
async def test_periodic_task_start_with_args() -> None:
    received: list[tuple[Any, ...]] = []

    @periodic_task(interval=0.02, immediate=True)
    async def worker(item: str, multiplier: int = 1) -> None:
        received.append((item, multiplier))

    worker.start("test-item", multiplier=3)
    await asyncio.sleep(0.03)
    worker.stop()

    assert len(received) >= 1
    assert received[0] == ("test-item", 3)


@pytest.mark.asyncio
async def test_periodic_task_method_binding() -> None:
    class Service:
        def __init__(self, multiplier: int) -> None:
            self.multiplier = multiplier
            self.counter = 0

        @periodic_task(interval=0.02, immediate=True)
        async def heartbeat(self) -> None:
            self.counter += self.multiplier

    service = Service(multiplier=5)
    # Check that descriptor caches instance on the object
    runner1 = service.heartbeat
    runner2 = service.heartbeat
    assert runner1 is runner2

    service.heartbeat.start()
    await asyncio.sleep(0.05)
    service.heartbeat.stop()

    assert service.heartbeat.is_stopped
    assert service.counter >= 10

    # Ensure counter stops incrementing after stop
    stopped_counter = service.counter
    await asyncio.sleep(0.05)
    assert service.counter == stopped_counter


@pytest.mark.asyncio
async def test_periodic_task_error_suppression_and_hook() -> None:
    errors_caught: list[Exception] = []
    run_count = 0

    def sync_error_hook(exc: Exception) -> None:
        errors_caught.append(exc)

    @periodic_task(
        interval=0.02,
        immediate=True,
        raise_exceptions=False,
        on_error=sync_error_hook,
    )
    async def failing_job() -> None:
        nonlocal run_count
        run_count += 1
        if run_count <= 2:
            raise RuntimeError(f"Failing run {run_count}")

    failing_job.start()
    await asyncio.sleep(0.07)
    failing_job.stop()

    assert len(errors_caught) == 2
    assert isinstance(errors_caught[0], RuntimeError)
    assert run_count >= 3  # Kept running after failures


@pytest.mark.asyncio
async def test_periodic_task_async_error_hook() -> None:
    async_errors: list[str] = []

    async def async_hook(exc: Exception) -> None:
        await asyncio.sleep(0.001)
        async_errors.append(str(exc))

    @periodic_task(
        interval=0.02,
        immediate=True,
        raise_exceptions=False,
        on_error=async_hook,
    )
    async def err_task() -> None:
        raise ValueError("async hook test")

    err_task.start()
    await asyncio.sleep(0.03)
    err_task.stop()

    assert len(async_errors) >= 1
    assert "async hook test" in async_errors[0]


@pytest.mark.asyncio
async def test_periodic_task_raise_exceptions() -> None:
    @periodic_task(interval=0.02, immediate=True, raise_exceptions=True)
    async def fatal_job() -> None:
        raise ZeroDivisionError("division by zero")

    fatal_job.start()
    assert fatal_job.task is not None

    with pytest.raises(ZeroDivisionError):
        await fatal_job.task

    assert fatal_job.is_stopped


@pytest.mark.asyncio
async def test_periodic_task_context_managers() -> None:
    async_count = 0

    @periodic_task(interval=0.02, immediate=True)
    async def async_cm_job() -> None:
        nonlocal async_count
        async_count += 1

    async with async_cm_job:
        assert async_cm_job.is_running
        await asyncio.sleep(0.05)

    assert async_cm_job.is_stopped
    assert async_count >= 2

    sync_count = 0

    @periodic_task(interval=0.02, immediate=True)
    async def sync_cm_job() -> None:
        nonlocal sync_count
        sync_count += 1

    with sync_cm_job:
        assert sync_cm_job.is_running
        await asyncio.sleep(0.05)

    assert sync_cm_job.is_stopped
    assert sync_count >= 2


@pytest.mark.asyncio
async def test_periodic_task_duration_support() -> None:
    ticks = 0

    @async_timer(interval=Duration("20ms"), immediate=True)
    async def duration_job() -> None:
        nonlocal ticks
        ticks += 1

    assert duration_job.interval == 0.02

    async with duration_job:
        await asyncio.sleep(0.05)

    assert ticks >= 2

    timer2 = AsyncTimer(duration_job._func, interval=Duration(1, TimeUnit.SECONDS))
    assert timer2.interval == 1.0


@pytest.mark.asyncio
async def test_cancel_all_tasks_integration() -> None:
    ticks = 0

    @periodic_task(interval=0.02, immediate=True)
    async def cancellable_job() -> None:
        nonlocal ticks
        ticks += 1

    current_test_task = asyncio.current_task()
    assert current_test_task is not None

    cancellable_job.start()
    assert cancellable_job.is_running
    await asyncio.sleep(0.03)

    assert cancellable_job.task is not None
    assert not cancellable_job.task.done()

    # Cancel all running tasks in loop
    await cancel_all_tasks(None, current_test_task)

    assert cancellable_job.is_stopped
    assert cancellable_job.task.cancelled()


@pytest.mark.asyncio
async def test_periodic_task_properties_and_idempotency() -> None:
    @periodic_task(interval=0.05, immediate=True, name="named_task")
    async def dummy() -> None:
        pass

    assert dummy.interval == 0.05
    assert dummy.immediate is True
    assert dummy.next_run_at is None
    assert dummy.last_run_at is None

    # Pause / resume when not started
    dummy.pause()
    dummy.resume()
    assert dummy.is_stopped

    dummy.start()
    assert dummy.next_run_at is not None
    # Calling start while running is idempotent
    dummy.start()
    assert dummy.is_running

    dummy.pause()
    assert dummy.is_paused
    # Calling pause while already paused is idempotent
    dummy.pause()
    assert dummy.is_paused

    # Calling resume while paused resumes
    dummy.resume()
    assert dummy.is_running
    # Calling resume while running is idempotent
    dummy.resume()
    assert dummy.is_running

    dummy.stop()
    assert dummy.is_stopped
    # Calling stop while stopped is idempotent
    dummy.stop()
    assert dummy.is_stopped


@pytest.mark.asyncio
async def test_periodic_task_stop_while_paused() -> None:
    @periodic_task(interval=0.05, immediate=True)
    async def dummy() -> None:
        pass

    dummy.start()
    await asyncio.sleep(0.01)
    dummy.pause()
    assert dummy.is_paused

    dummy.stop()
    assert dummy.is_stopped
    await asyncio.sleep(0.02)
    assert dummy.is_stopped


@pytest.mark.asyncio
async def test_periodic_task_descriptor_on_class() -> None:
    class Worker:
        @periodic_task(interval=0.05)
        async def work(self) -> str:
            return "done"

    # Access on class directly returns un-bound PeriodicTask
    assert isinstance(Worker.work, PeriodicTask)


@pytest.mark.asyncio
async def test_periodic_task_unassigned_func_errors() -> None:
    task = PeriodicTask()
    with pytest.raises(RuntimeError, match="no target function assigned"):
        await task.tick()

    with pytest.raises(RuntimeError, match="no target function assigned"):
        task.start()


@pytest.mark.asyncio
async def test_periodic_task_decorator_invalid_function() -> None:
    with pytest.raises(TypeError, match="must be a coroutine function"):
        decorator = cast(Any, periodic_task(interval=0.05))

        @decorator
        def sync_fn() -> None:
            pass


@pytest.mark.asyncio
async def test_periodic_task_error_hook_exception(caplog: pytest.LogCaptureFixture) -> None:
    def buggy_hook(exc: Exception) -> None:
        raise ValueError("Bug in hook")

    @periodic_task(
        interval=0.02,
        immediate=True,
        raise_exceptions=False,
        on_error=buggy_hook,
    )
    async def failing_worker() -> None:
        raise RuntimeError("Worker failed")

    failing_worker.start()
    await asyncio.sleep(0.04)
    failing_worker.stop()

    assert "Error in periodic task error handler" in caplog.text


def test_periodic_task_autostart_no_running_loop() -> None:
    async def dummy() -> None:
        pass

    task = PeriodicTask(dummy, interval=1.0, autostart=True)
    assert task.is_stopped


def test_periodic_task_nan_interval() -> None:
    async def dummy() -> None:
        pass

    with pytest.raises(ValueError, match="positive finite number"):
        PeriodicTask(dummy, interval=float("nan"))


@pytest.mark.asyncio
async def test_periodic_task_partial_coroutine() -> None:
    async def worker(prefix: str, suffix: str) -> str:
        return f"{prefix}-{suffix}"

    partial_fn = functools.partial(worker, "hello")
    task = PeriodicTask(partial_fn, interval=0.05)
    res = await task("world")
    assert res == "hello-world"


@pytest.mark.asyncio
async def test_periodic_task_rapid_stop_start() -> None:
    count = 0

    @periodic_task(interval=0.02, immediate=True)
    async def worker() -> None:
        nonlocal count
        count += 1

    worker.start()
    await asyncio.sleep(0.01)
    # Rapid stop followed immediately by start
    worker.stop()
    worker.start()
    assert worker.is_running

    # Yield control and sleep to ensure previous task's cancellation doesn't kill current task
    await asyncio.sleep(0.06)
    assert worker.is_running
    worker.stop()
    assert count >= 2


def test_periodic_task_repr() -> None:
    async def dummy() -> None:
        pass

    task = PeriodicTask(dummy, interval=2.5, name="my_task")
    assert repr(task) == "<PeriodicTask name='my_task' state=STOPPED interval=2.5 iterations=0>"
