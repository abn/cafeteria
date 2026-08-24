from __future__ import annotations

from types import TracebackType
from typing import TypeVar

T = TypeVar("T", bound="ContextMixin")

__all__ = ["ContextMixin"]


class ContextMixin:
    def __enter__(self: T) -> T:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass
