from __future__ import annotations

from os import getenv
from typing import Any
from typing import TypeVar
from typing import overload

T = TypeVar("T")

_UNSET = object()

_TRUTHY_STRINGS: set[str] = {
    "1",
    "enable",
    "enabled",
    "on",
    "t",
    "true",
    "y",
    "yes",
}

_FALSY_STRINGS: set[str] = {
    "0",
    "disable",
    "disabled",
    "f",
    "false",
    "n",
    "no",
    "off",
}

__all__ = ["boolify", "listify", "resolve_setting", "to_bool"]


# noinspection SpellCheckingInspection
def listify(arg: set[Any] | tuple[Any, ...] | list[Any] | T) -> list[Any] | list[T]:
    """
    Simple utility method to ensure an argument provided is a list. If the
    provided argument is not an instance of `list`, then we return [arg], else
    arg is returned.
    """
    if isinstance(arg, set | tuple):
        # if it is a set or tuple make it a list
        return list(arg)
    if not isinstance(arg, list):
        return [arg]
    return arg


def resolve_setting(
    default: T,
    arg_value: T | None = None,
    env_var: str | None = None,
    config_value: T | None = None,
) -> T | str:
    """
    Resolves a setting for a configuration option. The winning value is chosen
    from multiple methods of configuration, in the following order of priority
    (top first):

    - Explicitly passed argument
    - Environment variable
    - Configuration file entry
    - Default

    :param arg_value: Explicitly passed value
    :param env_var: Environment variable name
    :param config_value: Configuration entry
    :param default: Default value to if there are no overriding options
    :return: Configuration value
    """
    if arg_value is not None:
        return arg_value
    elif env_var is not None:
        env_value = getenv(env_var)
        if env_value is not None:
            return env_value
    if config_value is not None:
        return config_value
    return default


@overload
def to_bool(val: Any) -> bool: ...


@overload
def to_bool(val: Any, default: T) -> bool | T: ...


def to_bool(val: Any, default: Any = _UNSET) -> bool | Any:
    """
    Safely coerce a value (such as a string, integer, or boolean) to a boolean.

    Truthy values (case-insensitive string or native representation):
      - "true", "yes", "1", "on", "t", "y", "enable", "enabled", 1, True
    Falsy values (case-insensitive string or native representation):
      - "false", "no", "0", "off", "f", "n", "disable", "disabled", 0, False

    :param val: The value to coerce to boolean.
    :param default: Default value to return if coercion fails. If not specified,
                    a ValueError is raised for invalid values.
    :return: Coerced boolean or default value.
    :raises ValueError: If coercion fails and no default value was provided.
    """
    if isinstance(val, bool):
        return val

    if isinstance(val, (int, float)):
        if val == 1:
            return True
        if val == 0:
            return False
        if default is not _UNSET:
            return default
        raise ValueError(f"Cannot coerce numeric {val!r} to boolean.")

    if isinstance(val, (bytes, bytearray)):
        try:
            val = val.decode("utf-8")
        except UnicodeDecodeError as err:
            if default is not _UNSET:
                return default
            raise ValueError(f"Cannot coerce bytes {val!r} to boolean.") from err

    if isinstance(val, str):
        cleaned = val.strip().lower()
        if cleaned in _TRUTHY_STRINGS:
            return True
        if cleaned in _FALSY_STRINGS:
            return False
        if default is not _UNSET:
            return default
        raise ValueError(f"Cannot coerce string {val!r} to boolean.")

    if default is not _UNSET:
        return default
    raise ValueError(f"Cannot coerce {val!r} to boolean.")


boolify = to_bool
