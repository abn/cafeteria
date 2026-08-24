from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import ClassVar
from typing import TypeVar

from cafeteria.datastructs.units import BaseUnitClass


class DataMultiplier(Enum):
    k = 10**3
    M = 10**6
    G = 10**9
    T = 10**12
    P = 10**15
    E = 10**18
    Z = 10**21
    Y = 10**24
    Ki = 2**10
    Mi = 2**20
    Gi = 2**30
    Ti = 2**40
    Pi = 2**50
    Ei = 2**60


class DataBaseUnit(Enum):
    b = 1
    bit = 1
    B = 8
    byte = 8


DU = TypeVar("DU", bound="DataUnit")

_DATA_UNITS: dict[str, float | int] = {
    f"{multiplier}{base}": DataMultiplier[multiplier].value * DataBaseUnit[base].value
    for multiplier in DataMultiplier.__members__
    for base in DataBaseUnit.__members__
}
_DATA_UNITS.update({base: DataBaseUnit[base].value for base in DataBaseUnit.__members__})


class DataUnit(BaseUnitClass):
    """
    A data unit object internally stores the number of bits associated.
    Eg: DataUnit(1, 'byte') == 8
    """

    UNITS: ClassVar[Mapping[str, float | int]] = _DATA_UNITS

    def __new__(cls: type[DU], x: str | int | float, unit: str | None = None) -> DU:
        if unit is None:
            # noinspection PyUnresolvedReferences
            unit = DataBaseUnit.bit.name
        return super().__new__(cls, x, unit)


DRU = TypeVar("DRU", bound="DataRateUnit")

_DATA_RATE_UNITS: dict[str, float | int] = {
    f"{unit}{suffix}": DataUnit.UNITS[unit] for unit in DataUnit.UNITS for suffix in ["/s", "ps"]
}


class DataRateUnit(DataUnit):
    """
    A data rate unit object internally stores the number bits per second.
    """

    UNITS: ClassVar[Mapping[str, float | int]] = _DATA_RATE_UNITS

    def __new__(cls: type[DRU], x: str | int | float, unit: str | None = None) -> DRU:
        if unit is None:
            # noinspection PyUnresolvedReferences
            unit = f"{DataBaseUnit.bit.name}ps"
        return super().__new__(cls, x, unit)
