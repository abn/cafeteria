from enum import Enum

from cafe.datastructs.units import BaseUnitClass


class DataMultiplier(Enum):
    k = 10 ** 3
    M = 10 ** 6
    G = 10 ** 9
    T = 10 ** 12
    P = 10 ** 15
    E = 10 ** 18
    Z = 10 ** 21
    Y = 10 ** 24
    Ki = 2 ** 10
    Mi = 2 ** 20
    Gi = 2 ** 30
    Ti = 2 ** 40
    Pi = 2 ** 50
    Ei = 2 ** 60


class DataBaseUnit(Enum):
    b = 1
    bit = 1
    B = 8
    byte = 8


class DataUnit(BaseUnitClass):
    """
    A data unit object internally stores the number of bits associated.
    Eg: DataUnit(1, 'byte') == 8
    """
    UNITS = {
        '{}{}'.format(multiplier, base):
            DataMultiplier[multiplier].value * DataBaseUnit[base].value
        for multiplier in DataMultiplier.__members__
        for base in DataBaseUnit.__members__
    }
    UNITS.update({
        base: DataBaseUnit[base].value
        for base in DataBaseUnit.__members__
    })

    # noinspection PyInitNewSignature
    def __new__(cls, x, unit=None):
        if unit is None:
            # noinspection PyUnresolvedReferences
            unit = DataBaseUnit.bit.name
        return super(DataUnit, cls).__new__(cls, x, unit)


class DataRateUnit(DataUnit):
    """
    A data rate unit object internally stores the number bits per second.
    """
    UNITS = {
        '{}{}'.format(unit, suffix): DataUnit.UNITS[unit]
        for unit in DataUnit.UNITS
        for suffix in ['/s', 'ps']
    }

    # noinspection PyInitNewSignature
    def __new__(cls, x, unit=None):
        if unit is None:
            # noinspection PyUnresolvedReferences
            unit = '{}ps'.format(DataBaseUnit.bit.name)
        return super(DataUnit, cls).__new__(cls, x, unit)
