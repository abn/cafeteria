from __future__ import annotations

from os import getenv
from typing import Any
from typing import TypeVar

T = TypeVar("T")

__all__ = ["listify", "resolve_setting"]


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
