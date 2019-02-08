try:
    # noinspection PyUnresolvedReferences
    long
except NameError:
    # noinspection PyShadowingBuiltins
    long = int
