"""
Time duration parsing, unit conversions, and arithmetic utilities.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Mapping
from enum import Enum
from typing import Any
from typing import ClassVar
from typing import TypeVar

from cafeteria.datastructs.units import BaseUnitClass

NANOSECONDS = 1e-9
MICROSECONDS = 1e-6
MILLISECONDS = 1e-3
SECONDS = 1.0
MINUTES = 60.0 * SECONDS
HOURS = 60.0 * MINUTES
DAYS = 24.0 * HOURS
WEEKS = 7.0 * DAYS

__all__ = [
    "DAYS",
    "HOURS",
    "MICROSECONDS",
    "MILLISECONDS",
    "MINUTES",
    "NANOSECONDS",
    "SECONDS",
    "WEEKS",
    "Duration",
    "TimeUnit",
]


class TimeUnit(Enum):
    """
    Enumeration of standard time units with values equal to their duration in seconds.
    """

    NANOSECONDS = NANOSECONDS
    NANOSECOND = NANOSECONDS
    NS = NANOSECONDS

    MICROSECONDS = MICROSECONDS
    MICROSECOND = MICROSECONDS
    US = MICROSECONDS

    MILLISECONDS = MILLISECONDS
    MILLISECOND = MILLISECONDS
    MS = MILLISECONDS

    SECONDS = SECONDS
    SECOND = SECONDS
    SEC = SECONDS
    SECS = SECONDS
    S = SECONDS

    MINUTES = MINUTES
    MINUTE = MINUTES
    MIN = MINUTES
    MINS = MINUTES
    M = MINUTES

    HOURS = HOURS
    HOUR = HOURS
    HR = HOURS
    HRS = HOURS
    H = HOURS

    DAYS = DAYS
    DAY = DAYS
    D = DAYS

    WEEKS = WEEKS
    WEEK = WEEKS
    W = WEEKS


_TIME_UNITS: dict[str, float] = {
    # nanoseconds
    "ns": NANOSECONDS,
    "nanosecond": NANOSECONDS,
    "nanoseconds": NANOSECONDS,
    # microseconds
    "us": MICROSECONDS,
    "µs": MICROSECONDS,
    "μs": MICROSECONDS,
    "microsecond": MICROSECONDS,
    "microseconds": MICROSECONDS,
    # milliseconds
    "ms": MILLISECONDS,
    "millisecond": MILLISECONDS,
    "milliseconds": MILLISECONDS,
    # seconds
    "s": SECONDS,
    "sec": SECONDS,
    "secs": SECONDS,
    "second": SECONDS,
    "seconds": SECONDS,
    # minutes
    "m": MINUTES,
    "min": MINUTES,
    "mins": MINUTES,
    "minute": MINUTES,
    "minutes": MINUTES,
    # hours
    "h": HOURS,
    "hr": HOURS,
    "hrs": HOURS,
    "hour": HOURS,
    "hours": HOURS,
    # days
    "d": DAYS,
    "day": DAYS,
    "days": DAYS,
    # weeks
    "w": WEEKS,
    "week": WEEKS,
    "weeks": WEEKS,
}

_ISO8601_PATTERN = re.compile(
    r"^P(?:(?P<weeks>\d+(?:\.\d+)?)W)?(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?(?:(?P<minutes>\d+(?:\.\d+)?)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$"
)

_DURATION_TOKEN_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*([a-zA-Zµμ]+)")


def _parse_duration_string(s: str) -> float:
    s = s.strip()
    if not s:
        raise ValueError("Duration requires a non-empty string.")

    sign = 1.0
    if s.startswith("-"):
        sign = -1.0
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()

    if not s:
        raise ValueError("Duration requires a valid number and unit.")

    if s.upper().startswith("P"):
        iso_match = _ISO8601_PATTERN.match(s.upper())
        if iso_match:
            gd = iso_match.groupdict()
            if not any(gd.values()):
                raise ValueError(f"Invalid ISO-8601 duration format: {s!r}")
            total = 0.0
            if gd.get("weeks"):
                total += float(gd["weeks"]) * WEEKS
            if gd.get("days"):
                total += float(gd["days"]) * DAYS
            if gd.get("hours"):
                total += float(gd["hours"]) * HOURS
            if gd.get("minutes"):
                total += float(gd["minutes"]) * MINUTES
            if gd.get("seconds"):
                total += float(gd["seconds"]) * SECONDS
            return sign * total

    matches = list(_DURATION_TOKEN_PATTERN.finditer(s))
    if not matches:
        raise ValueError(
            f'Duration requires a number or a string in the format "<value> <unit>" (e.g. "1h 30m 15s", "90m"). Got: {s!r}'
        )

    cleaned = re.sub(r"[\s,]+|\band\b", "", s, flags=re.IGNORECASE)
    matched_str = "".join(f"{m.group(1)}{m.group(2)}" for m in matches)
    if cleaned != matched_str:
        raise ValueError(f"Invalid duration string: {s!r}")

    total = 0.0
    for m in matches:
        val_str, unit_str = m.group(1), m.group(2).lower()
        if unit_str not in _TIME_UNITS:
            raise ValueError(f"Unknown time unit {unit_str!r} in {s!r}")
        total += float(val_str) * _TIME_UNITS[unit_str]

    return sign * total


def _format_duration(seconds: float) -> str:
    if seconds == 0:
        return "0s"

    sign = "-" if seconds < 0 else ""
    abs_seconds = abs(seconds)

    total_ns = round(abs_seconds * 1_000_000_000)
    if total_ns == 0:
        return "0s"

    ns_in_w = 604_800 * 1_000_000_000
    ns_in_d = 86_400 * 1_000_000_000
    ns_in_h = 3_600 * 1_000_000_000
    ns_in_m = 60 * 1_000_000_000
    ns_in_s = 1 * 1_000_000_000
    ns_in_ms = 1_000_000
    ns_in_us = 1_000

    parts: list[str] = []
    rem = total_ns

    w = rem // ns_in_w
    if w:
        parts.append(f"{w}w")
        rem %= ns_in_w

    d = rem // ns_in_d
    if d:
        parts.append(f"{d}d")
        rem %= ns_in_d

    h = rem // ns_in_h
    if h:
        parts.append(f"{h}h")
        rem %= ns_in_h

    m = rem // ns_in_m
    if m:
        parts.append(f"{m}m")
        rem %= ns_in_m

    s = rem // ns_in_s
    if s:
        parts.append(f"{s}s")
        rem %= ns_in_s

    ms = rem // ns_in_ms
    if ms:
        parts.append(f"{ms}ms")
        rem %= ns_in_ms

    us = rem // ns_in_us
    if us:
        parts.append(f"{us}us")
        rem %= ns_in_us

    ns = rem
    if ns:
        parts.append(f"{ns}ns")

    return f"{sign}{' '.join(parts)}"


D = TypeVar("D", bound="Duration")


class Duration(BaseUnitClass):
    """
    A duration object internally stores the number of seconds as a float,
    providing human-readable time duration parsing and unit conversion.
    """

    UNITS: ClassVar[Mapping[str, float | int]] = _TIME_UNITS

    def __new__(
        cls: type[D],
        x: str | int | float | datetime.timedelta | Duration,
        unit: str | TimeUnit | None = None,
    ) -> D:
        val: float
        if isinstance(x, Duration):
            if unit is not None:
                raise ValueError(
                    "Cannot specify unit when creating Duration from an existing Duration."
                )
            val = float(x)
        elif isinstance(x, datetime.timedelta):
            if unit is not None:
                raise ValueError("Cannot specify unit when creating Duration from a timedelta.")
            val = x.total_seconds()
        elif isinstance(x, str):
            if unit is not None:
                factor = cls._resolve_unit_factor(unit)
                try:
                    val = float(x) * factor
                except ValueError as err:
                    raise ValueError(
                        f"Could not parse numeric string {x!r} with unit {unit!r}"
                    ) from err
            else:
                val = _parse_duration_string(x)
        elif isinstance(x, (int, float)):
            if unit is None:
                raise ValueError("No unit provided.")
            factor = cls._resolve_unit_factor(unit)
            val = float(x) * factor
        else:
            raise TypeError(f"Unsupported type for Duration: {type(x).__name__}")

        return float.__new__(cls, val)

    @classmethod
    def _resolve_unit_factor(cls, unit: str | TimeUnit) -> float:
        if isinstance(unit, TimeUnit):
            return float(unit.value)
        if isinstance(unit, str):
            unit_clean = unit.strip()
            if unit_clean.lower() in _TIME_UNITS:
                return _TIME_UNITS[unit_clean.lower()]
            if unit_clean.upper() in TimeUnit.__members__:
                return float(TimeUnit[unit_clean.upper()].value)
            raise ValueError(f"Unknown time unit: {unit!r}")
        raise TypeError(f"Unit must be a str or TimeUnit, got {type(unit).__name__}")

    @property
    def total_seconds(self) -> float:
        """Return total duration in seconds as a float."""
        return float(self)

    @property
    def timedelta(self) -> datetime.timedelta:
        """Return duration as a datetime.timedelta object."""
        return datetime.timedelta(seconds=self.total_seconds)

    def to_timedelta(self) -> datetime.timedelta:
        """Convert to datetime.timedelta."""
        return self.timedelta

    @classmethod
    def from_timedelta(cls: type[D], td: datetime.timedelta) -> D:
        """Create a Duration from a datetime.timedelta object."""
        return cls(td)

    @property
    def human_readable(self) -> str:
        """Return human-readable duration string representation (e.g. '1h 30m 15s')."""
        return _format_duration(float(self))

    def to_string(self) -> str:
        """Return human-readable duration string."""
        return self.human_readable

    def __str__(self) -> str:
        return self.human_readable

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.human_readable!r})"

    def __hash__(self) -> int:
        return hash(float(self))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Duration):
            return float(self) == float(other)
        if isinstance(other, datetime.timedelta):
            return self.total_seconds == other.total_seconds()
        if isinstance(other, (int, float)):
            return float(self) == float(other)
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        eq = self.__eq__(other)
        if eq is NotImplemented:
            return NotImplemented
        return not eq

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Duration):
            return float(self) < float(other)
        if isinstance(other, datetime.timedelta):
            return self.total_seconds < other.total_seconds()
        if isinstance(other, (int, float)):
            return float(self) < float(other)
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Duration):
            return float(self) <= float(other)
        if isinstance(other, datetime.timedelta):
            return self.total_seconds <= other.total_seconds()
        if isinstance(other, (int, float)):
            return float(self) <= float(other)
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Duration):
            return float(self) > float(other)
        if isinstance(other, datetime.timedelta):
            return self.total_seconds > other.total_seconds()
        if isinstance(other, (int, float)):
            return float(self) > float(other)
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Duration):
            return float(self) >= float(other)
        if isinstance(other, datetime.timedelta):
            return self.total_seconds >= other.total_seconds()
        if isinstance(other, (int, float)):
            return float(self) >= float(other)
        return NotImplemented

    def __add__(self, other: Any) -> Duration:
        if isinstance(other, Duration):
            return Duration(float(self) + float(other), TimeUnit.SECONDS)
        if isinstance(other, datetime.timedelta):
            return Duration(float(self) + other.total_seconds(), TimeUnit.SECONDS)
        if isinstance(other, (int, float)):
            return Duration(float(self) + float(other), TimeUnit.SECONDS)
        return NotImplemented

    def __radd__(self, other: Any) -> Duration:
        return self.__add__(other)

    def __sub__(self, other: Any) -> Duration:
        if isinstance(other, Duration):
            return Duration(float(self) - float(other), TimeUnit.SECONDS)
        if isinstance(other, datetime.timedelta):
            return Duration(float(self) - other.total_seconds(), TimeUnit.SECONDS)
        if isinstance(other, (int, float)):
            return Duration(float(self) - float(other), TimeUnit.SECONDS)
        return NotImplemented

    def __rsub__(self, other: Any) -> Duration:
        if isinstance(other, datetime.timedelta):
            return Duration(other.total_seconds() - float(self), TimeUnit.SECONDS)
        if isinstance(other, (int, float)):
            return Duration(float(other) - float(self), TimeUnit.SECONDS)
        return NotImplemented

    def __mul__(self, other: Any) -> Duration:
        if isinstance(other, (int, float)):
            return Duration(float(self) * float(other), TimeUnit.SECONDS)
        return NotImplemented

    def __rmul__(self, other: Any) -> Duration:
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> Any:
        if isinstance(other, Duration):
            return float(self) / float(other)
        if isinstance(other, datetime.timedelta):
            return float(self) / other.total_seconds()
        if isinstance(other, (int, float)):
            return Duration(float(self) / float(other), TimeUnit.SECONDS)
        return NotImplemented

    def __rtruediv__(self, other: Any) -> Any:
        if isinstance(other, datetime.timedelta):
            return other.total_seconds() / float(self)
        return NotImplemented

    def __floordiv__(self, other: Any) -> Any:
        if isinstance(other, Duration):
            return int(float(self) // float(other))
        if isinstance(other, datetime.timedelta):
            return int(float(self) // other.total_seconds())
        if isinstance(other, (int, float)):
            return Duration(float(self) // float(other), TimeUnit.SECONDS)
        return NotImplemented

    def __mod__(self, other: Any) -> Duration:
        if isinstance(other, Duration):
            return Duration(float(self) % float(other), TimeUnit.SECONDS)
        if isinstance(other, datetime.timedelta):
            return Duration(float(self) % other.total_seconds(), TimeUnit.SECONDS)
        if isinstance(other, (int, float)):
            return Duration(float(self) % float(other), TimeUnit.SECONDS)
        return NotImplemented

    def __neg__(self) -> Duration:
        return Duration(-float(self), TimeUnit.SECONDS)

    def __pos__(self) -> Duration:
        return Duration(float(self), TimeUnit.SECONDS)

    def __abs__(self) -> Duration:
        return Duration(abs(float(self)), TimeUnit.SECONDS)
