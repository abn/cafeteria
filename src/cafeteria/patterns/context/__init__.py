from __future__ import annotations

from collections.abc import Callable
from typing import Generic
from typing import ParamSpec
from typing import Protocol
from typing import TypeVar


class SessionProtocol(Protocol):
    def open(self) -> None:
        pass

    def close(self) -> None:
        pass


P = ParamSpec("P")
T = TypeVar("T", bound=SessionProtocol)


class SessionManager(Generic[P, T]):
    def __init__(self, factory: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None:
        self._kwargs = kwargs
        self._args = args
        self._factory = factory
        self.session: T | None = None

    def open(self) -> None:
        if self.session is None:
            self.session = self._factory(*self._args, **self._kwargs)

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
        self.session = None

    def __enter__(self) -> T | None:
        self.open()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
