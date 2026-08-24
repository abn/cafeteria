from __future__ import annotations

from collections.abc import Hashable
from typing import Any
from typing import ClassVar
from typing import cast

__all__ = ["Borg", "BorgStateManager"]


class BorgStateManager:
    """
    A special State Manager for Borg classes and child classes. This is what
    makes it possible for child classes to maintain their own state different
    to both parents, siblings and their own children.

    This itself implements the Borg pattern so that all its instances have a
    shared state.

    Each class state is mapped to the hash of the class itself.
    """

    __shared_state: ClassVar[dict[type[Borg], dict[Hashable, Any]]] = {}

    def __init__(self):
        self.__dict__ = cast(dict[str, Any], self.__shared_state)

    @classmethod
    def get_state(cls, clz: type[Borg]) -> dict[Hashable, Any]:
        """
        Retrieve the state of a given Class.
        """
        if clz not in cls.__shared_state:
            cls.__shared_state[clz] = clz.init_state() if hasattr(clz, "init_state") else {}
        return cls.__shared_state[clz]


class Borg:
    """
    A Borg pattern base class. Usable on its own or via inheritance. Uses
    `cafeteria.patterns.borg.BorgStateManager` internally to achieve state
    separation for children and grand children.

    See http://code.activestate.com/recipes/66531-singleton-we-dont-need-no-stinkin-singleton-the-bo/ for more # noqa
    information regarding the Borg Pattern.
    """

    def __init__(self):
        self.__dict__ = cast(dict[str, Any], self._shared_state)

    @classmethod
    def init_state(cls) -> dict[Hashable, Any]:
        return {}

    @property
    def _shared_state(self) -> dict[Hashable, Any]:
        return BorgStateManager.get_state(self.__class__)
