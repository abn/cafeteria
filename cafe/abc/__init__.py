from abc import ABCMeta


class AbstractClass(object):
    __metaclass__ = ABCMeta

    # noinspection PyUnresolvedReferences
    @classmethod
    def __subclasshook__(cls, other_class):
        return super(
            AbstractClass, cls).__subclasshook__(other_class) \
               and all(any(x in B.__dict__ for B in other_class.__mro__)
                       for x in cls.__abstractmethods__)
