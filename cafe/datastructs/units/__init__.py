from re import match


try:
    long
except NameError:
    # noinspection PyShadowingBuiltins
    long = int


class BaseUnitClass(float):
    UNITS = {}

    # noinspection PyInitNewSignature
    def __new__(cls, x, unit=None):
        if isinstance(x, str):
            units_regex = '|'.join(cls.UNITS.keys())
            m = match(r'^(\d+(.\d+)?) ?({})$'.format(units_regex), x)
            if m is None:
                raise ValueError(
                    '{} requires number or a string in the format "<value> '
                    '({})"'.format(cls.__name__, units_regex)
                )
            x = float(m.group(1)) * cls.UNITS.get(m.group(3))
        elif unit is None:
            raise ValueError('No unit provided.')
        else:
            x = x * cls.UNITS[unit]
        return super(BaseUnitClass, cls).__new__(cls, x)

    def __getattr__(self, item):
        if item in self.UNITS:
            # if unit is known convert to unit
            result = self * 1.0 / self.UNITS[item]
            rounded = long(result)
            return result if result != rounded else rounded
        raise AttributeError('{} is not a valid conversion unit'.format(item))
