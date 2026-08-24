from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cafeteria.asyncio.callbacks import Callback
from cafeteria.asyncio.callbacks import SimpleTriggerCallback
from cafeteria.asyncio.callbacks import trigger_callback


@pytest.mark.asyncio
async def test_trigger_callback_blocking(mocker: Any) -> None:
    m = mocker.Mock()

    result = trigger_callback(m, "foo", bar="baz")
    assert isinstance(result, asyncio.Future)

    await result
    m.assert_called_once_with("foo", bar="baz")


@pytest.mark.asyncio
async def test_trigger_callback_coroutine() -> None:
    call_args = []

    # using a real coroutine here as mocking will fail iscoroutine checks
    async def coroutine(*_, **__):
        call_args.append((_, __))

    result = trigger_callback(coroutine, "foo", bar="baz")
    assert isinstance(result, asyncio.Task)

    await result
    assert call_args == [(("foo",), dict(bar="baz"))]


@pytest.mark.asyncio
async def test_trigger_callback_callback(mocker: Any) -> None:
    m = mocker.Mock()
    cb = Callback(m, "foo", bar="baz")
    result = trigger_callback(cb, not_ignored=True)
    assert isinstance(result, asyncio.Future)

    await result
    m.assert_called_once_with(*cb.args, **cb.kwargs, not_ignored=True)


@pytest.mark.asyncio
async def test_trigger_callback_simple_trigger_callback(mocker: Any) -> None:
    m = mocker.Mock()
    cb = SimpleTriggerCallback(m, "foo", bar="baz")
    result = trigger_callback(cb, ignored=True)
    assert isinstance(result, asyncio.Future)

    await result
    m.assert_called_once_with(*cb.args, **cb.kwargs)
