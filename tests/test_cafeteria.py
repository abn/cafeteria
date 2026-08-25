from __future__ import annotations

from typing import Any

import pytest

from cafeteria.datastructs import Duration
from cafeteria.datastructs import Memory
from cafeteria.datastructs import MemoryUnit
from cafeteria.datastructs import TimeUnit
from cafeteria.datastructs.units import BaseUnitClass
from cafeteria.datastructs.units.data import DataRateUnit
from cafeteria.datastructs.units.data import DataUnit
from cafeteria.decorators import classproperty
from cafeteria.decorators import retry
from cafeteria.patterns import ContextMixin
from cafeteria.patterns import SessionManager
from cafeteria.patterns import get_by_path
from cafeteria.utilities import boolify
from cafeteria.utilities import listify
from cafeteria.utilities import resolve_setting
from cafeteria.utilities import to_bool


def test_memory_units() -> None:
    mem = Memory(1024, MemoryUnit.KB)
    assert mem == 1024 * 1024
    mem2 = Memory("1024 KB")
    assert mem2 == 1024 * 1024

    with pytest.raises(ValueError):
        Memory("invalid string")

    with pytest.raises(ValueError):
        Memory(1024)


def test_data_units() -> None:
    unit = DataUnit(1, "byte")
    assert unit == 8
    assert unit.byte == 1
    assert unit.bit == 8

    rate = DataRateUnit(100, "Mbps")
    assert rate == 100 * 10**6

    with pytest.raises(ValueError):
        DataUnit("invalid")

    with pytest.raises(ValueError):
        BaseUnitClass(100)


def test_duration_units() -> None:
    d = Duration("1h 30m 15s")
    assert d.total_seconds == 5415.0
    assert d == Duration(90, TimeUnit.MINUTES) + Duration(15, TimeUnit.SECONDS)
    assert d.hours == 1.5041666666666667
    assert d.seconds == 5415

    with pytest.raises(ValueError):
        Duration("invalid")

    with pytest.raises(ValueError):
        Duration(100)


def test_classproperty() -> None:
    class DummyClass:
        @classproperty
        def prop(cls: Any) -> str:  # noqa: N805
            return str(cls.__name__)

    assert DummyClass.prop == "DummyClass"


def test_get_by_path() -> None:
    data = {"a": {"b": {"c": 42}}}
    assert get_by_path(data, "a", "b", "c") == 42
    assert get_by_path(data, "a", "b", "d", default=0) == 0

    with pytest.raises(ValueError):
        get_by_path(data)


def test_utilities(monkeypatch: pytest.MonkeyPatch) -> None:
    assert listify("item") == ["item"]
    assert listify(["item"]) == ["item"]
    assert listify(("item",)) == ["item"]
    assert listify({"item"}) == ["item"]

    monkeypatch.setenv("TEST_CAFETERIA_SETTING", "env_val")
    assert resolve_setting(default="def", env_var="TEST_CAFETERIA_SETTING") == "env_val"
    assert resolve_setting(default="def", arg_value="arg") == "arg"
    assert resolve_setting(default="def", env_var="NON_EXISTENT_CAFETERIA_ENV_XYZ") == "def"
    assert resolve_setting(default="def", config_value="cfg") == "cfg"


def test_to_bool_truthy() -> None:
    truthy_cases = [
        "true",
        "True",
        "TRUE",
        "yes",
        "Yes",
        "YES",
        "1",
        "on",
        "On",
        "ON",
        "t",
        "T",
        "y",
        "Y",
        "enable",
        "Enable",
        "enabled",
        "ENABLED",
        True,
        1,
        1.0,
        b"true",
        b"1",
        b"yes",
        bytearray(b"on"),
        "  true  ",
        "\t 1 \n",
        "  ENABLE  ",
    ]
    for case in truthy_cases:
        assert to_bool(case) is True
        assert boolify(case) is True


def test_to_bool_falsy() -> None:
    falsy_cases = [
        "false",
        "False",
        "FALSE",
        "no",
        "No",
        "NO",
        "0",
        "off",
        "Off",
        "OFF",
        "f",
        "F",
        "n",
        "N",
        "disable",
        "Disable",
        "disabled",
        "DISABLED",
        False,
        0,
        0.0,
        b"false",
        b"0",
        b"off",
        bytearray(b"no"),
        "  false  ",
        "\n 0 \t",
        "  DISABLED  ",
    ]
    for case in falsy_cases:
        assert to_bool(case) is False
        assert boolify(case) is False


def test_to_bool_default() -> None:
    assert to_bool("invalid", default=False) is False
    assert to_bool("invalid", default=True) is True
    assert to_bool(None, default=None) is None
    assert to_bool(None, default=False) is False
    assert to_bool(42, default=True) is True
    assert to_bool(b"\xff\xfe", default=False) is False
    assert to_bool([], default="fallback") == "fallback"
    assert to_bool({}, default=None) is None

    assert boolify("invalid", default=False) is False


def test_to_bool_errors() -> None:
    invalid_cases = [
        "invalid",
        "maybe",
        "",
        "   ",
        None,
        2,
        -1,
        1.5,
        b"\xff\xfe",
        [],
        {},
        object(),
    ]
    for case in invalid_cases:
        with pytest.raises(ValueError):
            to_bool(case)
        with pytest.raises(ValueError):
            boolify(case)


def test_boolify_alias() -> None:
    assert boolify is to_bool


def test_context_mixin() -> None:
    class MyContext(ContextMixin):
        pass

    with MyContext() as ctx:
        assert isinstance(ctx, MyContext)


def test_session_manager() -> None:
    class DummySession:
        def __init__(self) -> None:
            self.is_open = False

        def open(self) -> None:
            self.is_open = True

        def close(self) -> None:
            self.is_open = False

    manager = SessionManager(DummySession)
    with manager as session:
        assert session is not None
        assert session.is_open
    assert manager.session is None


def test_retry_decorator() -> None:
    calls = 0

    @retry(attempts=3, backoff=0.0)
    def flaky_func() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise ConnectionError("transient")
        return "success"

    assert flaky_func() == "success"
    assert calls == 2


async def test_retry_async_decorator() -> None:
    calls = 0

    @retry(attempts=3, backoff=0.0, retry_on=(ConnectionError,))
    async def flaky_async() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise ConnectionError("transient")
        return "async success"

    assert await flaky_async() == "async success"
    assert calls == 2
