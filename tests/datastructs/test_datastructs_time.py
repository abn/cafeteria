from __future__ import annotations

from datetime import timedelta
from typing import Any
from typing import cast

import pytest

from cafeteria.datastructs.units import Duration
from cafeteria.datastructs.units import TimeUnit
from cafeteria.datastructs.units.time import DAYS
from cafeteria.datastructs.units.time import HOURS
from cafeteria.datastructs.units.time import MICROSECONDS
from cafeteria.datastructs.units.time import MILLISECONDS
from cafeteria.datastructs.units.time import MINUTES
from cafeteria.datastructs.units.time import NANOSECONDS
from cafeteria.datastructs.units.time import SECONDS
from cafeteria.datastructs.units.time import WEEKS


def test_user_example() -> None:
    d = Duration("1h 30m 15s")
    assert d.total_seconds == 5415.0
    assert d == Duration(90, TimeUnit.MINUTES) + Duration(15, TimeUnit.SECONDS)


class TestDurationParsing:
    def test_single_tokens(self) -> None:
        assert Duration("10s").total_seconds == 10.0
        assert Duration("90m").total_seconds == 5400.0
        assert Duration("1.5h").total_seconds == 5400.0
        assert Duration("2d").total_seconds == 172800.0
        assert Duration("3w").total_seconds == 1814400.0
        assert Duration("100ms").total_seconds == 0.1
        assert pytest.approx(Duration("500us").total_seconds) == 0.0005
        assert pytest.approx(Duration("500µs").total_seconds) == 0.0005
        assert pytest.approx(Duration("500μs").total_seconds) == 0.0005
        assert pytest.approx(Duration("200ns").total_seconds) == 2e-7

    def test_multi_tokens(self) -> None:
        d = Duration("1h 30m 15s")
        assert d.total_seconds == 5415.0

        d_compact = Duration("1h30m15s")
        assert d_compact.total_seconds == 5415.0

        d_words = Duration("1 hour, 30 minutes and 15 seconds")
        assert d_words.total_seconds == 5415.0

        d_complex = Duration("1w 2d 3h 4m 5s 600ms 700us 800ns")
        expected = (
            1 * WEEKS
            + 2 * DAYS
            + 3 * HOURS
            + 4 * MINUTES
            + 5 * SECONDS
            + 600 * MILLISECONDS
            + 700 * MICROSECONDS
            + 800 * NANOSECONDS
        )
        assert pytest.approx(d_complex.total_seconds, rel=1e-9) == expected

    def test_negative_strings(self) -> None:
        d = Duration("-1h 30m 15s")
        assert d.total_seconds == -5415.0

        d2 = Duration("-90m")
        assert d2.total_seconds == -5400.0

        d3 = Duration("+1h 30m")
        assert d3.total_seconds == 5400.0

    def test_iso8601_strings(self) -> None:
        assert Duration("PT1H30M15S").total_seconds == 5415.0
        assert Duration("P1DT2H3M4S").total_seconds == 86400.0 + 7200.0 + 180.0 + 4.0
        assert Duration("PT0.5S").total_seconds == 0.5
        assert Duration("P1W").total_seconds == 604800.0
        assert Duration("P2D").total_seconds == 172800.0
        assert Duration("PT3H").total_seconds == 10800.0
        assert Duration("PT4M").total_seconds == 240.0
        assert Duration("PT5S").total_seconds == 5.0
        assert Duration("-PT1H").total_seconds == -3600.0
        assert Duration("PT0S").total_seconds == 0.0


class TestDurationConstruction:
    def test_with_time_unit_enum(self) -> None:
        assert Duration(90, TimeUnit.MINUTES).total_seconds == 5400.0
        assert Duration(15, TimeUnit.SECONDS).total_seconds == 15.0
        assert Duration(1.5, TimeUnit.HOURS).total_seconds == 5400.0
        assert Duration(1, TimeUnit.DAYS).total_seconds == 86400.0
        assert Duration(2, TimeUnit.WEEKS).total_seconds == 1209600.0
        assert Duration(500, TimeUnit.MILLISECONDS).total_seconds == 0.5
        assert pytest.approx(Duration(100, TimeUnit.MICROSECONDS).total_seconds) == 0.0001
        assert pytest.approx(Duration(50, TimeUnit.NANOSECONDS).total_seconds) == 5e-8

        # Short aliases
        assert Duration(10, TimeUnit.S).total_seconds == 10.0
        assert Duration(10, TimeUnit.M).total_seconds == 600.0
        assert Duration(10, TimeUnit.H).total_seconds == 36000.0
        assert Duration(10, TimeUnit.D).total_seconds == 864000.0
        assert Duration(10, TimeUnit.W).total_seconds == 6048000.0
        assert Duration(10, TimeUnit.MS).total_seconds == 0.01
        assert pytest.approx(Duration(10, TimeUnit.US).total_seconds) == 0.00001
        assert pytest.approx(Duration(10, TimeUnit.NS).total_seconds) == 1e-8

    def test_with_string_unit(self) -> None:
        assert Duration(90, "minutes").total_seconds == 5400.0
        assert Duration(90, "MINUTES").total_seconds == 5400.0
        assert Duration(90, "m").total_seconds == 5400.0
        assert Duration(15, "s").total_seconds == 15.0
        assert Duration("90", TimeUnit.MINUTES).total_seconds == 5400.0
        assert Duration("90", "minutes").total_seconds == 5400.0

    def test_with_timedelta(self) -> None:
        td = timedelta(hours=1, minutes=30, seconds=15)
        d = Duration(td)
        assert d.total_seconds == 5415.0
        assert Duration.from_timedelta(td) == d

    def test_copy_constructor(self) -> None:
        d1 = Duration("1h 30m")
        d2 = Duration(d1)
        assert d1 == d2
        assert d2.total_seconds == 5400.0


class TestDurationErrors:
    def test_no_unit_provided_for_number(self) -> None:
        with pytest.raises(ValueError, match="No unit provided"):
            Duration(90)

        with pytest.raises(ValueError, match="No unit provided"):
            Duration(0)

    def test_invalid_strings(self) -> None:
        with pytest.raises(ValueError):
            Duration("")

        with pytest.raises(ValueError):
            Duration("   ")

        with pytest.raises(ValueError):
            Duration("-")

        with pytest.raises(ValueError):
            Duration("+")

        with pytest.raises(ValueError):
            Duration("invalid")

        with pytest.raises(ValueError):
            Duration("1h invalid")

        with pytest.raises(ValueError):
            Duration("10 unknownunit")

        with pytest.raises(ValueError):
            Duration("P")

        with pytest.raises(ValueError):
            Duration("not_a_number", TimeUnit.SECONDS)

    def test_invalid_units(self) -> None:
        with pytest.raises(ValueError, match="Unknown time unit"):
            Duration(10, "unknown_unit")

        with pytest.raises(TypeError, match="Unit must be a str or TimeUnit"):
            Duration(10, cast(Any, 123))

    def test_invalid_types(self) -> None:
        with pytest.raises(TypeError):
            Duration(cast(Any, None))

        with pytest.raises(TypeError):
            Duration(cast(Any, [1, 2, 3]))

    def test_unit_with_duration_or_timedelta_raises(self) -> None:
        d = Duration("1h")
        with pytest.raises(ValueError, match="Cannot specify unit"):
            Duration(d, TimeUnit.SECONDS)

        with pytest.raises(ValueError, match="Cannot specify unit"):
            Duration(timedelta(hours=1), TimeUnit.SECONDS)

    def test_invalid_attribute(self) -> None:
        d = Duration("1h")
        with pytest.raises(AttributeError, match="not a valid conversion unit"):
            _ = d.non_existent_unit_attribute


class TestDurationConversions:
    def test_attribute_conversions(self) -> None:
        d = Duration("1h 30m")
        assert d.total_seconds == 5400.0
        assert d.seconds == 5400
        assert d.minutes == 90
        assert d.hours == 1.5
        assert d.days == 5400 / 86400
        assert d.weeks == 5400 / 604800
        assert d.milliseconds == 5400000
        assert d.microseconds == 5400000000
        assert d.nanoseconds == 5400000000000

        # Short attributes
        assert d.s == 5400
        assert d.m == 90
        assert d.h == 1.5

    def test_timedelta_property(self) -> None:
        d = Duration("1h 30m 15s")
        assert d.timedelta == timedelta(hours=1, minutes=30, seconds=15)
        assert d.to_timedelta() == timedelta(hours=1, minutes=30, seconds=15)


class TestDurationArithmetic:
    def test_addition(self) -> None:
        d1 = Duration(90, TimeUnit.MINUTES)
        d2 = Duration(15, TimeUnit.SECONDS)
        res = d1 + d2
        assert isinstance(res, Duration)
        assert res.total_seconds == 5415.0

        # Add timedelta
        td = timedelta(seconds=15)
        res_td = d1 + td
        assert isinstance(res_td, Duration)
        assert res_td.total_seconds == 5415.0

        # Radd timedelta
        res_rtd = td + d1
        assert isinstance(res_rtd, Duration)
        assert res_rtd.total_seconds == 5415.0

        # Add float/int seconds
        res_num = d1 + 15
        assert isinstance(res_num, Duration)
        assert res_num.total_seconds == 5415.0

    def test_subtraction(self) -> None:
        d1 = Duration("2h")
        d2 = Duration("30m")
        res = d1 - d2
        assert isinstance(res, Duration)
        assert res.total_seconds == 5400.0

        res_td = d1 - timedelta(minutes=30)
        assert isinstance(res_td, Duration)
        assert res_td.total_seconds == 5400.0

        res_rtd = timedelta(hours=2) - d2
        assert isinstance(res_rtd, Duration)
        assert res_rtd.total_seconds == 5400.0

        res_num = d1 - 1800
        assert isinstance(res_num, Duration)
        assert res_num.total_seconds == 5400.0

    def test_multiplication(self) -> None:
        d = Duration("30m")
        res1 = d * 3
        assert isinstance(res1, Duration)
        assert res1.total_seconds == 5400.0

        res2 = 3 * d
        assert isinstance(res2, Duration)
        assert res2.total_seconds == 5400.0

    def test_division(self) -> None:
        d = Duration("1h")
        res_scalar = d / 2
        assert isinstance(res_scalar, Duration)
        assert res_scalar.total_seconds == 1800.0

        ratio = d / Duration("30m")
        assert isinstance(ratio, float)
        assert ratio == 2.0

        ratio_td = d / timedelta(minutes=30)
        assert isinstance(ratio_td, float)
        assert ratio_td == 2.0

        # timedelta / float(Duration) returns timedelta in python standard library
        td_divided = timedelta(hours=1) / d
        assert isinstance(td_divided, timedelta)
        assert td_divided == timedelta(seconds=1)

    def test_floordiv_and_mod(self) -> None:
        d = Duration("1h 15m")
        res_floordiv = d // Duration("30m")
        assert isinstance(res_floordiv, int)
        assert res_floordiv == 2

        res_floordiv_scalar = d // 2
        assert isinstance(res_floordiv_scalar, Duration)
        assert res_floordiv_scalar.total_seconds == 2250.0

        res_floordiv_td = d // timedelta(minutes=30)
        assert isinstance(res_floordiv_td, int)
        assert res_floordiv_td == 2

        res_mod = d % Duration("30m")
        assert isinstance(res_mod, Duration)
        assert res_mod.total_seconds == 900.0

    def test_unary_operations(self) -> None:
        d = Duration("1h")
        neg = -d
        assert isinstance(neg, Duration)
        assert neg.total_seconds == -3600.0

        pos = +d
        assert isinstance(pos, Duration)
        assert pos.total_seconds == 3600.0

        abs_d = abs(neg)
        assert isinstance(abs_d, Duration)
        assert abs_d.total_seconds == 3600.0

    def test_unsupported_operands(self) -> None:
        d = Duration("1h")
        with pytest.raises(TypeError):
            _ = d + "invalid"

        with pytest.raises(TypeError):
            _ = d - "invalid"

        with pytest.raises(TypeError):
            _ = d * "invalid"

        with pytest.raises(TypeError):
            _ = d / "invalid"

        with pytest.raises(TypeError):
            _ = d // "invalid"

        with pytest.raises(TypeError):
            _ = d % "invalid"

        with pytest.raises(TypeError):
            _ = "invalid" + d

        with pytest.raises(TypeError):
            _ = "invalid" - d

        with pytest.raises(TypeError):
            _ = "invalid" / d

    def test_ordering_unsupported(self) -> None:
        d = Duration("1h")
        with pytest.raises(TypeError):
            _ = d < "invalid"

        with pytest.raises(TypeError):
            _ = d <= "invalid"

        with pytest.raises(TypeError):
            _ = d > "invalid"

        with pytest.raises(TypeError):
            _ = d >= "invalid"


class TestDurationComparisons:
    def test_equality(self) -> None:
        d1 = Duration("90m")
        d2 = Duration("1h 30m")
        assert d1 == d2
        assert d1 == timedelta(hours=1, minutes=30)
        assert d1 == 5400.0
        assert d1 == 5400

        assert d1 != Duration("1h")
        assert d1 != timedelta(hours=1)
        assert d1 != 3600
        assert d1 != "not a duration"

    def test_ordering(self) -> None:
        d1 = Duration("1h")
        d2 = Duration("2h")

        assert d1 < d2
        assert d1 <= d2
        assert d2 > d1
        assert d2 >= d1

        assert d1 < timedelta(hours=2)
        assert d1 <= timedelta(hours=1)
        assert d2 > timedelta(hours=1)
        assert d2 >= timedelta(hours=2)

        assert d1 < 7200
        assert d1 <= 3600
        assert d2 > 3600
        assert d2 >= 7200

    def test_hashability(self) -> None:
        d1 = Duration("1h")
        d2 = Duration("60m")
        s = {d1, d2}
        assert len(s) == 1
        assert d1 in s
        assert d2 in s


class TestDurationFormatting:
    def test_formatting_strings(self) -> None:
        assert str(Duration("1h 30m 15s")) == "1h 30m 15s"
        assert repr(Duration("1h 30m 15s")) == "Duration('1h 30m 15s')"
        assert Duration("1h 30m 15s").human_readable == "1h 30m 15s"
        assert Duration("1h 30m 15s").to_string() == "1h 30m 15s"

    def test_zero_duration(self) -> None:
        assert str(Duration(0, TimeUnit.SECONDS)) == "0s"
        assert repr(Duration(0, TimeUnit.SECONDS)) == "Duration('0s')"

    def test_sub_second_formatting(self) -> None:
        assert str(Duration("500ms")) == "500ms"
        assert str(Duration("1.5s")) == "1s 500ms"
        assert str(Duration("500us")) == "500us"
        assert str(Duration("100ns")) == "100ns"

    def test_negative_formatting(self) -> None:
        assert str(Duration("-1h 30m")) == "-1h 30m"
