# noinspection PyUnresolvedReferences
from cafe.abc.compat import abstractclassmethod  # noqa F401


# noinspection PyPep8Naming,SpellCheckingInspection
class classproperty(property):
    """
    A decorator that behaves like @property except that operates
    on classes rather than instances.

    Original Implementation: sqlalchemy.util.langhelpers.classproperty
    """

    def __init__(self, fget, *arg, **kw):
        super(classproperty, self).__init__(fget, *arg, **kw)
        self.__doc__ = fget.__doc__

    # noinspection PyMethodOverriding,PyArgumentList,PyMethodParameters
    def __get__(desc, self, cls):
        return desc.fget(cls)
