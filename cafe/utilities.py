from six import string_types


def listify(arg):
    """
    Simple utility method to ensure an argument provided is a list. If the provider argument is not an instance of
    `list`, then we return [arg], else arg is returned.

    :type arg: list
    :rtype: list
    """
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
