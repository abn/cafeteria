from __future__ import annotations

from typing import Any

import pytest

import cafeteria
from cafeteria.datastructs import Memory
from cafeteria.datastructs import MemoryUnit
from cafeteria.datastructs.units import BaseUnitClass
from cafeteria.datastructs.units.data import DataRateUnit
from cafeteria.datastructs.units.data import DataUnit
from cafeteria.decorators import classproperty
from cafeteria.patterns import ContextMixin
from cafeteria.patterns import SessionManager
from cafeteria.patterns import get_by_path
from cafeteria.utilities import listify
from cafeteria.utilities import resolve_setting


def test_package_version() -> None:
    assert cafeteria.__version__ == "0.23.0a0"


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


def test_utilities() -> None:
    assert listify("item") == ["item"]
    assert listify(["item"]) == ["item"]
    assert listify(("item",)) == ["item"]
    assert listify({"item"}) == ["item"]

    assert resolve_setting(default="def", arg_value="arg") == "arg"
    assert resolve_setting(default="def", env_var="NON_EXISTENT_CAFETERIA_ENV_XYZ") == "def"
    assert resolve_setting(default="def", config_value="cfg") == "cfg"


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
