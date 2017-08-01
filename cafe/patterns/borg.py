class BorgStateManager(object):
    """
    A special State Manager for Borg classes and child classes. This is what
    makes it possible for child classes to maintain their own state different
    to both parents, siblings and their own children.

    This itself implements the Borg pattern so that all its instances have a
    shared state.

    Each class state is mapped to the the hash of the class itself.
    """
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    @classmethod
    def get_state(cls, clz):
        """
        Retrieve the state of a given Class.

        :param clz: types.ClassType
        :return: Class state.
        :rtype: dict
        """
        if clz not in cls.__shared_state:
            cls.__shared_state[clz] = clz.init_state() \
                if hasattr(clz, 'init_state') \
                else {}
        return cls.__shared_state[clz]


class Borg(object):
    """
    A Borg pattern base class. Usable on its own or via inheritance. Uses
    `cafe.patterns.borg.BorgStateManager` internally to achieve state
    separation for children and grand children.

    See http://code.activestate.com/recipes/66531-singleton-we-dont-need-no-stinkin-singleton-the-bo/ for more # noqa
    information regarding the Borg Pattern.
    """

    def __init__(self):
        self.__dict__ = self._shared_state

    @classmethod
    def init_state(cls):
        return {}

    @property
    def _shared_state(self):
        return BorgStateManager.get_state(self.__class__)
