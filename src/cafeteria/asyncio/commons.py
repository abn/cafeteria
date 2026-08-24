from __future__ import annotations

import asyncio
import contextlib
import signal
import warnings
from asyncio import AbstractEventLoop
from typing import Any


async def cancel_all_tasks(
    loop: AbstractEventLoop | None = None, *ignore: asyncio.Task[Any]
) -> None:
    """
    Cancel and wait for all running tasks in the specified or current event loop.

    :param loop: Optional `AbstractEventLoop` to add signal handlers for, if not
        provided, running loop is used.
    :param ignore: If specified, these tasks are ignored even when running.
    """
    for task in asyncio.all_tasks(loop):
        if task is asyncio.current_task() or task in ignore:
            continue
        if not (task.done() or task.cancelled()):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def cancel_tasks_on_termination(
    loop: AbstractEventLoop | None = None, *args: signal.Signals | int | str
) -> None:
    """
    Helper method to add a signal handlers for specified or current event loop. Handlers
    are registered for SIGINT, SIGTERM and any additional signals passed in.

    :param loop: Optional `AbstractEventLoop` to add signal handlers for, if not
        provided, running loop is used.
    :param args: Additional signals to register cancellation for.
    """
    if loop is None:
        loop = asyncio.get_running_loop()

    for sig in {signal.SIGINT, signal.SIGTERM, *args}:
        if not isinstance(sig, signal.Signals):
            if isinstance(sig, int):
                sig = signal.Signals(sig)
            elif isinstance(sig, str):
                try:
                    sig = getattr(signal, sig)
                except AttributeError:
                    raise ValueError(f"Invalid signal name {sig}") from None
            else:
                raise ValueError(
                    f"Signal should be one of signal.Signals, int or str, got {type(sig)}"
                )
        loop.add_signal_handler(
            sig, lambda: asyncio.ensure_future(cancel_all_tasks(loop=loop), loop=loop)
        )


def handle_signals(event_loop: AbstractEventLoop, *signames: str) -> None:
    warnings.warn(
        f"Use {cancel_tasks_on_termination.__name__} instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return cancel_tasks_on_termination(event_loop, *signames)
