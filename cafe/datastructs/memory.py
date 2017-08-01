from enum import Enum
from re import match

BYTES = 1
KB = 1024 * BYTES
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB


class MemoryUnit(Enum):
    BYTES = BYTES
    KB = KB
    MB = MB
    GB = GB
    TB = TB


class Memory(long):
    # noinspection PyInitNewSignature
    def __new__(cls, x, unit=None):
        if isinstance(x, str):
            units_regex = '|'.join(MemoryUnit.__members__.keys())
            m = match(r'^(\d+) ?({})$'.format(units_regex), x)
            if m is None:
                raise ValueError(
                    '{} requires am integer or a string in the format "<value>'
                    ' ({})"'.format(Memory.__class__.__name__, units_regex)
                )
            x = int(m.group(1)) * MemoryUnit.__members__.get(m.group(2)).value
        elif unit is None:
            raise ValueError('No unit provided.')
        else:
            x = x * unit.value
        # noinspection PyTypeChecker
        return super(Memory, cls).__new__(cls, x)
