from __future__ import annotations

from abc import ABCMeta

__all__ = ["AbstractClass"]


class AbstractClass(metaclass=ABCMeta):  # noqa: B024
    @classmethod
    def __subclasshook__(cls, other_class: type) -> bool:
        res = super().__subclasshook__(other_class)
        if res is NotImplemented:
            return all(
                any(x in B.__dict__ for B in other_class.__mro__)
                for x in getattr(cls, "__abstractmethods__", [])
            )
        return bool(res)
