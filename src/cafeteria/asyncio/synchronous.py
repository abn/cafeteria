from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any


def execute_async_method(coroutine: Coroutine[Any, Any, Any]) -> Any | asyncio.Task[Any]:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        return loop.create_task(coroutine)
    else:
        return asyncio.run(coroutine)
