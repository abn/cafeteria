from abc import ABCMeta


class AbstractClass:
    __metaclass__ = ABCMeta

    @classmethod
    def __subclasshook__(cls, other_class):
        return super().__subclasshook__(other_class) and all(
            any(x in B.__dict__ for B in other_class.__mro__)
            for x in getattr(cls, "__abstractmethods__", [])
        )
