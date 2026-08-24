from __future__ import annotations

import re
from enum import IntEnum

BYTES = 1
KB = 1024 * BYTES
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB

__all__ = [
    "BYTES",
    "GB",
    "KB",
    "MB",
    "TB",
    "Memory",
    "MemoryUnit",
]


class MemoryUnit(IntEnum):
    BYTES = BYTES
    KB = KB
    MB = MB
    GB = GB
    TB = TB


class Memory(int):
    def __new__(cls, x: str | int, unit: MemoryUnit | None = None) -> Memory:
        if isinstance(x, str):
            units_regex = "|".join(MemoryUnit.__members__.keys())
            m = re.match(rf"^(\d+)\s*({units_regex})$", x)
            if m is None:
                raise ValueError(
                    f'{cls.__name__} requires an integer or a string in the format "<value> ({units_regex})"'
                )
            x = int(m.group(1)) * MemoryUnit[m.group(2)].value
        elif unit is None:
            raise ValueError("No unit provided.")
        else:
            x = x * unit.value
        # noinspection PyTypeChecker
        return super().__new__(cls, x)
