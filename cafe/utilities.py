from os import getenv
from six import string_types


# noinspection SpellCheckingInspection
def listify(arg):
    """
    Simple utility method to ensure an argument provided is a list. If the
    provider argument is not an instance of `list`, then we return [arg], else
    arg is returned.

    :type arg: list
    :rtype: list
    """
    if isinstance(arg, (set, tuple)):
        # if it is a set or tuple make it a list
        return list(arg)
    if not isinstance(arg, list):
        return [arg]
    return arg


def is_str(arg):
    """
    A py2/3 compatible 'is string' check.

    :type arg:
    :rtype:
    """
    return isinstance(arg, string_types)


def resolve_setting(default, arg_value=None, env_var=None, config_value=None):
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
    :type env_var: string or None
    :param config_value: Configuration entry
    :param default: Default value to if there are no overriding options
    :return: Configuration value
    """
    if arg_value is not None:
        return arg_value
    else:
        env_value = getenv(env_var)
        if env_value is not None:
            return env_value
        else:
            if config_value is not None:
                return config_value
            else:
                return default
