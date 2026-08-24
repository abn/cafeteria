from __future__ import annotations

import asyncio
import signal
from typing import Any

import pytest

from cafeteria.asyncio.commons import cancel_all_tasks
from cafeteria.asyncio.commons import cancel_tasks_on_termination


# noinspection PyUnresolvedReferences,PyProtectedMember
def ensure_signal_handlers_registered(
    loop: asyncio.AbstractEventLoop, *args: signal.Signals
) -> None:
    signal_handlers = getattr(loop, "_signal_handlers", {})
    assert len(signal_handlers) == 2 + len(args)

    # ensure default signal handlers registered added
    assert signal.SIGINT in signal_handlers
    assert signal.SIGTERM in signal_handlers

    for arg in args:
        assert arg in signal_handlers


def test_handle_signals(recwarn: Any) -> None:
    # noinspection PyDeprecation
    from cafeteria.asyncio.commons import handle_signals

    loop = asyncio.new_event_loop()
    handle_signals(loop)
    ensure_signal_handlers_registered(loop)

    # ensure a deprecation warning was issued
    assert len(recwarn) == 1
    w = recwarn.pop(DeprecationWarning)
    assert issubclass(w.category, DeprecationWarning)
    assert str(w.message) == "Use cancel_tasks_on_termination instead"
    loop.close()


def test_cancel_tasks_on_termination_default() -> None:
    loop = asyncio.new_event_loop()
    cancel_tasks_on_termination(loop, signal.SIGABRT)
    ensure_signal_handlers_registered(loop, signal.SIGABRT)
    loop.close()


def test_cancel_tasks_on_termination_int() -> None:
    loop = asyncio.new_event_loop()
    cancel_tasks_on_termination(loop, 6)
    ensure_signal_handlers_registered(loop, signal.SIGABRT)
    loop.close()


def test_cancel_tasks_on_termination_str() -> None:
    loop = asyncio.new_event_loop()
    cancel_tasks_on_termination(loop, "SIGABRT")
    ensure_signal_handlers_registered(loop, signal.SIGABRT)
    loop.close()


def test_cancel_tasks_on_termination_invalid_type(mocker: Any) -> None:
    loop = asyncio.new_event_loop()
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        cancel_tasks_on_termination(loop, mocker.Mock())
    loop.close()


def test_cancel_tasks_on_termination_invalid_int() -> None:
    loop = asyncio.new_event_loop()
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        cancel_tasks_on_termination(loop, 9999)
    loop.close()


def test_cancel_tasks_on_termination_invalid_str() -> None:
    loop = asyncio.new_event_loop()
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        cancel_tasks_on_termination(loop, "FOOBAR")
    loop.close()


@pytest.mark.asyncio
async def test_cancel_all_tasks() -> None:
    async def infinity():
        try:
            while True:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    test_task = asyncio.current_task()
    assert test_task is not None
    task = asyncio.ensure_future(infinity())

    # ensure task is running
    assert not (task.done() or task.cancelled())

    await cancel_all_tasks(None, test_task)
    assert task.cancelled()

    # current task was ignored
    assert not (test_task.done() or test_task.cancelled())
