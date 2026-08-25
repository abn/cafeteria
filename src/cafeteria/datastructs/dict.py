from __future__ import annotations

import copy
import json
from collections.abc import Iterator
from collections.abc import Mapping
from os.path import isfile
from typing import Any

from cafeteria.patterns.borg import Borg

__all__ = [
    "AttributeDict",
    "BorgDict",
    "CaseInsensitiveDict",
    "DeepAttributeDict",
    "DeepCaseInsensitiveDict",
    "DeepFrozenAttributeDict",
    "DeepMergingDict",
    "FrozenAttributeDict",
    "JSONAttributeDict",
    "MergingDict",
    "ReadOnlyDict",
]


class AttributeDict(dict[str, Any]):
    """
    A dictionary implementation that allows for all keys to be used as an
    attribute. In this implementation we do proper get/setattr override here,
    no self.__dict__ mambo jumbo.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __getattr__(self, item: str) -> Any:
        if item in self:
            return self[item]
        raise AttributeError(f"Could not get attr: '{item}' from '{self}'")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class DeepAttributeDict(AttributeDict):
    """
    A DeepAttributeDict is an AttributeDict of which dict objects at all depths
    are converted to DeepAttributeDict.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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
    def disabled_types(self) -> tuple[type, ...]:
        return ()

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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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


class ReadOnlyDict(dict[Any, Any]):
    """
    An immutable dictionary mapping that prevents modification after initialization.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_hash", None)

    def __setitem__(self, key: Any, value: Any) -> None:
        raise TypeError(f"'{self.__class__.__name__}' object does not support item assignment")

    def __delitem__(self, key: Any) -> None:
        raise TypeError(f"'{self.__class__.__name__}' object does not support item deletion")

    def clear(self) -> None:
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def pop(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def popitem(self) -> Any:
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def setdefault(self, key: Any, default: Any = None) -> Any:
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def __ior__(self, other: Any) -> Any:  # type: ignore[override]
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def __hash__(self) -> int:
        h = getattr(self, "_hash", None)
        if h is None:
            h = hash(frozenset(self.items()))
            object.__setattr__(self, "_hash", h)
        return h

    def copy(self) -> ReadOnlyDict:
        return self.__class__(self)

    def __copy__(self) -> ReadOnlyDict:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> ReadOnlyDict:
        return self.__class__(
            {copy.deepcopy(k, memo): copy.deepcopy(v, memo) for k, v in self.items()}
        )


class FrozenAttributeDict(ReadOnlyDict):
    """
    An immutable counterpart to AttributeDict for safe runtime configuration objects.
    Allows attribute access to dictionary keys, but prevents any item or attribute modification.
    """

    def __getattr__(self, item: str) -> Any:
        if item in self:
            return self[item]
        raise AttributeError(f"Could not get attr: '{item}' from '{self}'")

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return
        raise AttributeError(f"'{self.__class__.__name__}' object attribute '{key}' is read-only")

    def __delattr__(self, item: str) -> None:
        if item.startswith("_"):
            object.__delattr__(self, item)
            return
        raise AttributeError(f"'{self.__class__.__name__}' object attribute '{item}' is read-only")


class DeepFrozenAttributeDict(FrozenAttributeDict):
    """
    A DeepFrozenAttributeDict is a FrozenAttributeDict of which dict objects at all depths
    are converted to DeepFrozenAttributeDict.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._deep_init()

    def _deep_init(self) -> None:
        for key, value in list(self.items()):
            if isinstance(value, dict) and not isinstance(value, DeepFrozenAttributeDict):
                dict.__setitem__(self, key, DeepFrozenAttributeDict(value))


class CaseInsensitiveDict(dict[str, Any]):
    """
    Header- and key-insensitive dictionary supporting attribute and item lookups.
    Preserves original key casings for iteration and serialization while enabling
    case-insensitive key lookups and snake_case/kebab-case attribute access.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        object.__setattr__(self, "_keys", {})
        self.update(*args, **kwargs)

    @staticmethod
    def _normalize_key(key: Any) -> Any:
        return key.casefold() if isinstance(key, str) else key

    def _resolve_key(self, key: Any) -> Any:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            return keys_map[norm]
        if isinstance(key, str):
            hyphen_norm = self._normalize_key(key.replace("_", "-"))
            if hyphen_norm in keys_map:
                return keys_map[hyphen_norm]
        return None

    def __getitem__(self, key: Any) -> Any:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            actual_key = keys_map[norm]
            return super().__getitem__(actual_key)
        raise KeyError(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            old_actual = keys_map[norm]
            if old_actual != key:
                super().__delitem__(old_actual)
        keys_map[norm] = key
        super().__setitem__(key, value)

    def __delitem__(self, key: Any) -> None:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            actual_key = keys_map.pop(norm)
            super().__delitem__(actual_key)
        else:
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        return norm in keys_map

    def get(self, key: Any, default: Any = None) -> Any:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            actual_key = keys_map[norm]
            return super().__getitem__(actual_key)
        return default

    def setdefault(self, key: Any, default: Any = None) -> Any:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            return super().__getitem__(keys_map[norm])
        self[key] = default
        return default

    def pop(self, key: Any, *args: Any) -> Any:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        norm = self._normalize_key(key)
        if norm in keys_map:
            actual_key = keys_map.pop(norm)
            return super().pop(actual_key)
        if args:
            return args[0]
        raise KeyError(key)

    def popitem(self) -> tuple[Any, Any]:
        key, value = super().popitem()
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        keys_map.pop(self._normalize_key(key), None)
        return key, value

    def clear(self) -> None:
        keys_map: dict[Any, Any] = getattr(self, "_keys", {})
        keys_map.clear()
        super().clear()

    def update(self, *args: Any, **kwargs: Any) -> None:
        for arg in args:
            if isinstance(arg, Mapping):
                for k, v in arg.items():
                    self[k] = v
            elif hasattr(arg, "keys"):
                for k in arg.keys():  # noqa: SIM118
                    self[k] = arg[k]
            else:
                for k, v in arg:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def copy(self) -> CaseInsensitiveDict:
        return self.__class__(self)

    def __copy__(self) -> CaseInsensitiveDict:
        return self.__class__(self)

    def __deepcopy__(self, memo: dict[int, Any]) -> CaseInsensitiveDict:
        new_instance = self.__class__()
        memo[id(self)] = new_instance
        for k, v in self.items():
            new_instance[copy.deepcopy(k, memo)] = copy.deepcopy(v, memo)
        return new_instance

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mapping):
            if len(self) != len(other):
                return False
            keys_map: dict[Any, Any] = getattr(self, "_keys", {})
            for k, v in other.items():
                norm = self._normalize_key(k)
                if norm not in keys_map:
                    return False
                if self[k] != v:
                    return False
            return True
        return super().__eq__(other)

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")
        resolved = self._resolve_key(item)
        if resolved is not None:
            return self[resolved]
        raise AttributeError(f"Could not get attr: '{item}' from '{self}'")

    def __setattr__(self, key: str, value: Any) -> None:
        if key == "_keys" or key.startswith("_"):
            object.__setattr__(self, key, value)
            return
        resolved = self._resolve_key(key)
        if resolved is not None:
            self[resolved] = value
        else:
            self[key] = value

    def __delattr__(self, item: str) -> None:
        if item == "_keys" or item.startswith("_"):
            object.__delattr__(self, item)
            return
        resolved = self._resolve_key(item)
        if resolved is not None:
            del self[resolved]
        else:
            raise AttributeError(f"Could not delete attr: '{item}' from '{self}'")


class DeepCaseInsensitiveDict(CaseInsensitiveDict):
    """
    A DeepCaseInsensitiveDict is a CaseInsensitiveDict of which dict objects at all depths
    are converted to DeepCaseInsensitiveDict.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._deep_init()

    def _deep_init(self) -> None:
        for key, value in list(self.items()):
            if isinstance(value, dict) and not isinstance(value, DeepCaseInsensitiveDict):
                self[key] = DeepCaseInsensitiveDict(value)

    def __setitem__(self, key: Any, value: Any) -> None:
        if isinstance(value, dict) and not isinstance(value, DeepCaseInsensitiveDict):
            value = DeepCaseInsensitiveDict(value)
        super().__setitem__(key, value)
