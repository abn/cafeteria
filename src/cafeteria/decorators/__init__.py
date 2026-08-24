from __future__ import annotations

from collections.abc import Callable
from typing import Any


class classproperty(property):  # noqa: N801
    """A decorator that behaves like @property except that operates
    on classes rather than instances.

    Original Implementation: sqlalchemy.util.langhelpers.classproperty

    """

    fget: Callable[[Any], Any]

    def __init__(self, fget: Callable[[Any], Any], *arg: Any, **kw: Any):
        super().__init__(fget, *arg, **kw)
        self.__doc__ = fget.__doc__

    def __get__(self, obj: Any, cls: type | None = None) -> Any:
        return self.fget(cls)
