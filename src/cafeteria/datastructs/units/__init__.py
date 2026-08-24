from __future__ import annotations

import re
from collections.abc import Mapping
from typing import ClassVar
from typing import TypeVar

T = TypeVar("T", bound="BaseUnitClass")

__all__ = ["BaseUnitClass"]


class BaseUnitClass(float):
    UNITS: ClassVar[Mapping[str, float | int]] = {}

    # noinspection PyInitNewSignature
    def __new__(cls: type[T], x: str | int | float, unit: str | None = None) -> T:
        val: float
        if isinstance(x, str):
            units_regex = "|".join(cls.UNITS.keys())
            m = re.match(rf"^(\d+(.\d+)?) ?({units_regex})$", x)
            if m is None:
                raise ValueError(
                    f'{cls.__name__} requires number or a string in the format "<value> '
                    f'({units_regex})"'
                )
            val = float(m.group(1)) * cls.UNITS[m.group(3)]
        elif unit is None:
            raise ValueError("No unit provided.")
        else:
            val = float(x) * cls.UNITS[unit]
        return super().__new__(cls, val)

    def __getattr__(self, item: str) -> float | int:
        if item in self.UNITS:
            # if unit is known convert to unit
            result = self * 1.0 / self.UNITS[item]
            rounded = int(result)
            return result if result != rounded else rounded
        raise AttributeError(f"{item} is not a valid conversion unit")
