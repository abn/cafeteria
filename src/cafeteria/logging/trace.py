from __future__ import annotations

import logging
from typing import Any

TRACE: int = 5


logging.addLevelName(TRACE, "TRACE")
setattr(logging, "TRACE", TRACE)  # noqa: B010


def trace(self: logging.Logger, msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Log 'msg % args' with severity 'TRACE'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.trace("Houston, we have a %s", "thorny problem", exc_info=1)
    """
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)


class TraceEnabledLogger(logging.Logger):
    trace = trace


setattr(logging.Logger, "trace", trace)  # noqa: B010

# noinspection PyUnresolvedReferences,PyProtectedMember
LOGGING_LEVELS: dict[int, str] = getattr(
    logging, "_levelToName", getattr(logging, "_levelNames", {})
)
