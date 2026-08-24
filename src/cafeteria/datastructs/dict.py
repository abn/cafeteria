from __future__ import annotations

import copy
import json
from collections.abc import Iterator
from os.path import isfile
from typing import Any

from cafeteria.patterns.borg import Borg


class AttributeDict(dict):
    """
    A dictionary implementation that allows for all keys to be used as an
    attribute. In this implementation we do proper get/setattr override here,
    no self.__dict__ mambo jumbo.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, item: str) -> Any:
        if item in self:
            return self[item]
        raise AttributeError(f"Could not get attr: '{item}' from '{self}'")

    def __setattr__(self, key, value):
        self[key] = value


class DeepAttributeDict(AttributeDict):
    """
    A DeepAttributeDict is an AttributeDict of which dict objects at all depths
    are converted to DeepAttributeDict.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deep_init()

    def _deep_init(self) -> None:
        for key, value in self.items():
            if isinstance(value, dict) and not isinstance(value, AttributeDict):
                self[key] = DeepAttributeDict(value)


class MergingDict(AttributeDict):
    """
    A MergingDict is an AttributeDict whose attribute/item values are always
    merged if the rvalue implements an update or append method. If the rvalue
    is not merge-able, it is simply replaced.
    """

    @property
    def disabled_types(self) -> tuple:
        return tuple()

    def replace(self, key: str, value: Any) -> None:
        """
        Convenience method provided as a way to replace a value mapped by a
        key.This is required since a MergingDict always merges via assignment
        of item/attribute.
        """
        super().__setitem__(key, value)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """
        A special update method to handle merging of dict objects. For all
        other iterable objects, we use the parent class update method. For
        other objects, we simply make use of the internal merging logic.
        """
        if args:
            other = args[0]
            if isinstance(other, dict):
                for key in other:
                    self[key] = other[key]
            else:
                # noinspection PyTypeChecker
                super().update(other)

        for key, val in kwargs.items():
            self._merge(key, val)

    def _merge_method(self, key: str) -> str | None:
        """
        Identify a merge compatible method available in self[key]. Currently, we
        support 'update' and 'append'.

        :param key: Attribute name or item key
        :return: Method name usable to merge a value into the instance mapped
                by key
        :rtype: str
        """
        if key in self:
            obj = self[key]
            if isinstance(obj, self.disabled_types):
                return None
            for method in ["update", "append"]:
                if hasattr(obj, method):
                    return method
        return None

    def _merge(self, key: str, value: Any) -> None:
        """
        Internal merge logic implementation to allow merging of values when
        setting attributes/items.

        :param key: Attribute name or item key
        :type key: str
        :param value: Value to set attribute/item as.
        :type value: object
        :rtype: None
        """
        method = self._merge_method(key)
        if method is not None and isinstance(self[key], type(value)):
            # strings are special, update methods like set.update looks for
            # iterables
            if method == "update" and isinstance(value, str):
                value = [value]
            if method == "append" and isinstance(self[key], list) and isinstance(value, list):
                # if rvalue is a list and given object is a list, we expect all
                # values to be appended
                method = "extend"
            getattr(self[key], method)(value)
            return

        super().__setitem__(key, value)

    def __setitem__(self, key: str, value: Any) -> None:
        self._merge(key, value)

    def __setattr__(self, key: str, value: Any) -> None:
        self._merge(key, value)


class DeepMergingDict(MergingDict):
    """
    A DeepMergingDict is a MergingDict of which dict objects at all depths are
    converted to DeepMergingDicts.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deep_init()

    @staticmethod
    def _should_cast(value: Any) -> bool:
        return isinstance(value, dict) and not isinstance(value, MergingDict)

    def _deep_init(self) -> None:
        for key, value in self.items():
            if self._should_cast(value):
                self.replace(key, self.__class__(value))

    def replace(self, key: str, value: Any) -> None:
        if self._should_cast(value):
            value = self.__class__(value)
        super().replace(key, value)

    def update(self, *args: Any, **kwargs: Any) -> None:
        if args:
            other = args[0]
            if self._should_cast(other):
                other = self.__class__(other)
            super().update(other, **kwargs)
        else:
            super().update(**kwargs)


class BorgDict(Borg, dict[str, Any]):
    """
    A dict implementing the Borg Pattern. This can be extended via
    inheritance. In this implementation the dict itself is not used. All
    actions are mapped to the Borg shared state.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.update(*args, **kwargs)

    def update(self, *args: Any, **kwargs: Any) -> None:
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key: str, value: Any) -> None:
        self.__dict__[key] = value

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __delitem__(self, key: str) -> None:
        del self.__dict__[key]

    def __repr__(self) -> str:
        return repr(self.__dict__)

    def __str__(self) -> str:
        return str(self.__dict__)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __contains__(self, k: object) -> bool:
        return k in self.__dict__

    def keys(self) -> Any:
        return self.__dict__.keys()

    def get(self, *args: Any, **kwargs: Any) -> Any:
        return self.__dict__.get(*args, **kwargs)

    def pop(self, *args: Any, **kwargs: Any) -> Any:
        return self.__dict__.pop(*args, **kwargs)


class JSONAttributeDict(AttributeDict):
    """
    :type source: str or dict or cafeteria.datastructs.dict.JSONAttributeDict
    """

    def __init__(self, source: str | dict[str, Any] | JSONAttributeDict) -> None:
        super().__init__()

        try:
            self.update(json.loads(source) if isinstance(source, str) else copy.deepcopy(source))
        except ValueError:
            if isinstance(source, str) and isfile(source):
                with open(source) as sf:
                    self.update(json.load(sf))
            else:
                raise ValueError(source) from None

    @property
    def pretty(self) -> str:
        return json.dumps(self, indent=2)

    def __str__(self) -> str:
        return self.pretty

    def __repr__(self) -> str:
        return self.pretty
