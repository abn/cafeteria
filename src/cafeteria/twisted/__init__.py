from __future__ import annotations

from typing import Any

__all__ = ["async_sleep"]

try:
    from twisted.internet import defer  # ty: ignore[unresolved-import]
    from twisted.internet import reactor  # ty: ignore[unresolved-import]

    def async_sleep(seconds: int | float) -> Any:
        """
        An asynchronous sleep function using twisted.

        Source: https://twistedmatrix.com/pipermail/twisted-python/2009-October/020788.html
        """
        d = defer.Deferred()
        reactor.callLater(seconds, d.callback, seconds)
        return d

except ImportError:
    pass
