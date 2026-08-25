import copy
import json

import pytest

from cafeteria.datastructs.dict import AttributeDict
from cafeteria.datastructs.dict import BorgDict
from cafeteria.datastructs.dict import CaseInsensitiveDict
from cafeteria.datastructs.dict import DeepAttributeDict
from cafeteria.datastructs.dict import DeepCaseInsensitiveDict
from cafeteria.datastructs.dict import DeepFrozenAttributeDict
from cafeteria.datastructs.dict import DeepMergingDict
from cafeteria.datastructs.dict import FrozenAttributeDict
from cafeteria.datastructs.dict import JSONAttributeDict
from cafeteria.datastructs.dict import MergingDict
from cafeteria.datastructs.dict import ReadOnlyDict


@pytest.fixture
def simple_dict():
    return {"dict": {"one": 1, "nested": {"a": "a"}}, "list": [1]}


@pytest.fixture
def simple_dict_update():
    return {"dict": {"two": 2, "nested": {"b": "b"}}, "list": [2, 3]}


class TestMergingDict:
    def test_simple_merge(self, simple_dict, simple_dict_update):
        d = MergingDict(simple_dict)
        d.update(simple_dict_update)
        assert d == {
            "dict": {"one": 1, "two": 2, "nested": {"b": "b"}},
            "list": [1, 2, 3],
        }

    def test_merge_with_key(self, simple_dict):
        d = MergingDict(simple_dict)
        d["dict"] = {"two": 2}
        d["list"] = [2, 3]
        assert d == {
            "dict": {"one": 1, "two": 2, "nested": {"a": "a"}},
            "list": [1, 2, 3],
        }

    def test_changed_type_value(self, simple_dict):
        d = MergingDict(simple_dict)
        d.update({"dict": 0})
        assert d == {"dict": 0, "list": [1]}

        d["dict"] = {"z": "z"}
        assert d["dict"] == {"z": "z"}


class ListDisabledDeepMergingDict(DeepMergingDict):
    @property
    def disabled_types(self):
        return (list,)


class TestDeepMergingDict:
    def test_simple_deep_merge(self, simple_dict, simple_dict_update):
        d = DeepMergingDict(simple_dict)
        d.update(simple_dict_update)
        assert d == {
            "dict": {"one": 1, "two": 2, "nested": {"a": "a", "b": "b"}},
            "list": [1, 2, 3],
        }

    def test_simple_deep_merge_no_list(self, simple_dict, simple_dict_update):
        d = ListDisabledDeepMergingDict(simple_dict)
        d.update(simple_dict_update)
        assert d == {
            "dict": {"one": 1, "two": 2, "nested": {"a": "a", "b": "b"}},
            "list": [2, 3],
        }


class TestReadOnlyDict:
    def test_initialization_and_read(self):
        d = ReadOnlyDict({"a": 1, "b": 2}, c=3)
        assert d["a"] == 1
        assert d["b"] == 2
        assert d["c"] == 3
        assert d.get("a") == 1
        assert d.get("missing", 42) == 42
        assert "a" in d
        assert "missing" not in d
        assert len(d) == 3
        assert set(d.keys()) == {"a", "b", "c"}
        assert set(d.values()) == {1, 2, 3}
        assert set(d.items()) == {("a", 1), ("b", 2), ("c", 3)}
        assert list(d) == ["a", "b", "c"]

    def test_mutations_raise_type_error(self):
        d = ReadOnlyDict({"a": 1})

        with pytest.raises(TypeError, match="does not support item assignment"):
            d["a"] = 2
        with pytest.raises(TypeError, match="does not support item assignment"):
            d["b"] = 3

        with pytest.raises(TypeError, match="does not support item deletion"):
            del d["a"]

        with pytest.raises(TypeError, match="is read-only"):
            d.clear()

        with pytest.raises(TypeError, match="is read-only"):
            d.pop("a")

        with pytest.raises(TypeError, match="is read-only"):
            d.popitem()

        with pytest.raises(TypeError, match="is read-only"):
            d.setdefault("a", 1)

        with pytest.raises(TypeError, match="is read-only"):
            d.update({"b": 2})

        with pytest.raises(TypeError, match="is read-only"):
            d |= {"b": 2}

    def test_hashable_when_values_hashable(self):
        d1 = ReadOnlyDict({"a": 1, "b": 2})
        d2 = ReadOnlyDict({"b": 2, "a": 1})
        assert hash(d1) == hash(d2)

        s = {d1}
        assert d2 in s

        mapping = {d1: "config"}
        assert mapping[d2] == "config"

    def test_hash_fails_when_unhashable(self):
        d = ReadOnlyDict({"list": [1, 2, 3]})
        with pytest.raises(TypeError):
            hash(d)

    def test_copy_and_deepcopy(self):
        d = ReadOnlyDict({"a": 1, "nested": {"x": 10}})
        copied = copy.copy(d)
        assert copied is d

        shallow = d.copy()
        assert shallow == d
        assert isinstance(shallow, ReadOnlyDict)

        deep = copy.deepcopy(d)
        assert deep == d
        assert isinstance(deep, ReadOnlyDict)
        assert deep["nested"] is not d["nested"]


class TestFrozenAttributeDict:
    def test_attribute_access(self):
        d = FrozenAttributeDict({"host": "localhost", "port": 8080})
        assert d.host == "localhost"
        assert d.port == 8080
        assert d["host"] == "localhost"

    def test_missing_attribute_raises(self):
        d = FrozenAttributeDict({"host": "localhost"})
        with pytest.raises(AttributeError, match="Could not get attr: 'port'"):
            _ = d.port

    def test_attribute_mutation_raises(self):
        d = FrozenAttributeDict({"host": "localhost"})
        with pytest.raises(AttributeError, match="attribute 'host' is read-only"):
            d.host = "remote"

        with pytest.raises(AttributeError, match="attribute 'new_attr' is read-only"):
            d.new_attr = "val"

        with pytest.raises(AttributeError, match="attribute 'host' is read-only"):
            del d.host

    def test_private_attribute_allowed(self):
        d = FrozenAttributeDict({"host": "localhost"})
        d._private_field = "ok"
        assert d._private_field == "ok"
        del d._private_field
        assert not hasattr(d, "_private_field")

    def test_item_mutation_raises(self):
        d = FrozenAttributeDict({"host": "localhost"})
        with pytest.raises(TypeError, match="does not support item assignment"):
            d["host"] = "remote"

    def test_hashable(self):
        d = FrozenAttributeDict({"host": "localhost", "port": 8080})
        assert hash(d) is not None
        assert {d: "server"}[d] == "server"


class TestDeepFrozenAttributeDict:
    def test_deep_conversion(self):
        d = DeepFrozenAttributeDict(
            {
                "server": {"host": "localhost", "port": 8080},
                "database": {"credentials": {"user": "admin"}},
            }
        )
        assert isinstance(d.server, DeepFrozenAttributeDict)
        assert isinstance(d.database.credentials, DeepFrozenAttributeDict)
        assert d.server.host == "localhost"
        assert d.database.credentials.user == "admin"

    def test_deep_immutability(self):
        d = DeepFrozenAttributeDict({"server": {"host": "localhost"}})
        with pytest.raises(AttributeError, match="attribute 'host' is read-only"):
            d.server.host = "other"
        with pytest.raises(TypeError, match="does not support item assignment"):
            d.server["host"] = "other"


class CustomKeyMapping:
    def __init__(self, data):
        self._data = data

    def keys(self):
        return self._data.keys()

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, item):
        return self._data[item]


class TestCaseInsensitiveDict:
    def test_case_insensitive_access(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json", "Accept": "text/html"})
        assert d["Content-Type"] == "application/json"
        assert d["content-type"] == "application/json"
        assert d["CONTENT-TYPE"] == "application/json"
        assert d.get("content-type") == "application/json"
        assert d.get("CONTENT-TYPE") == "application/json"
        assert "content-type" in d
        assert "Content-Type" in d
        assert "CONTENT-TYPE" in d

    def test_non_string_keys(self):
        d = CaseInsensitiveDict()
        d[123] = "number"
        assert d[123] == "number"
        assert 123 in d
        assert d.get(123) == "number"
        assert d.pop(123) == "number"
        assert 123 not in d

    def test_preserves_original_key_casing(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json", "X-Request-ID": "123"})
        assert list(d.keys()) == ["Content-Type", "X-Request-ID"]
        assert list(d.items()) == [("Content-Type", "application/json"), ("X-Request-ID", "123")]

    def test_key_update_overwrites_existing(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json"})
        d["content-type"] = "text/plain"
        assert d["Content-Type"] == "text/plain"
        assert d["content-type"] == "text/plain"
        assert len(d) == 1
        assert list(d.keys()) == ["content-type"]

    def test_deletion(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json", "Host": "example.com"})
        del d["content-type"]
        assert "Content-Type" not in d
        assert "content-type" not in d
        assert len(d) == 1

        with pytest.raises(KeyError):
            del d["content-type"]

    def test_pop(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json"})
        val = d.pop("CONTENT-TYPE")
        assert val == "application/json"
        assert len(d) == 0
        assert d.pop("missing", "default") == "default"
        with pytest.raises(KeyError):
            d.pop("missing")

    def test_popitem(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json"})
        k, v = d.popitem()
        assert k == "Content-Type"
        assert v == "application/json"
        assert len(d) == 0
        assert "content-type" not in d

    def test_setdefault(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json"})
        assert d.setdefault("CONTENT-TYPE", "text/html") == "application/json"
        assert d.setdefault("X-New-Header", "new-value") == "new-value"
        assert d["x-new-header"] == "new-value"

    def test_clear(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json"})
        d.clear()
        assert len(d) == 0
        assert "content-type" not in d

    def test_update_variants(self):
        d = CaseInsensitiveDict()
        d.update({"Content-Type": "application/json"})
        assert d["content-type"] == "application/json"

        d.update([("Authorization", "Bearer token")])
        assert d["authorization"] == "Bearer token"

        d.update(CustomKeyMapping({"X-Custom": "custom_val"}))
        assert d["x-custom"] == "custom_val"

        d.update(Accept="text/plain")
        assert d["accept"] == "text/plain"

    def test_attribute_access_and_mutation(self):
        d = CaseInsensitiveDict(
            {
                "Content-Type": "application/json",
                "user_agent": "Mozilla/5.0",
                "host": "localhost",
            }
        )
        # Kebab-to-snake and case insensitivity
        assert d.content_type == "application/json"
        assert d.Content_Type == "application/json"
        assert d.user_agent == "Mozilla/5.0"
        assert d.User_Agent == "Mozilla/5.0"
        assert d.host == "localhost"
        assert d.Host == "localhost"

        # Attribute assignment updating existing header
        d.content_type = "text/html"
        assert d["Content-Type"] == "text/html"
        assert d.content_type == "text/html"

        # Attribute assignment creating new key
        d.x_custom_header = "custom"
        assert d["x_custom_header"] == "custom"
        assert d.x_custom_header == "custom"

        # Attribute deletion
        del d.content_type
        assert "Content-Type" not in d
        with pytest.raises(AttributeError):
            del d.content_type

    def test_private_attribute_handling(self):
        d = CaseInsensitiveDict({"host": "localhost"})
        d._private = "priv"
        assert d._private == "priv"
        del d._private
        with pytest.raises(AttributeError):
            _ = d._missing_private

    def test_missing_attribute_raises(self):
        d = CaseInsensitiveDict({"host": "localhost"})
        with pytest.raises(AttributeError, match="Could not get attr: 'port'"):
            _ = d.port

    def test_equality(self):
        d1 = CaseInsensitiveDict({"Content-Type": "application/json", "Host": "localhost"})
        d2 = {"content-type": "application/json", "host": "localhost"}
        assert d1 == d2
        assert d2 == d1

        d3 = CaseInsensitiveDict({"CONTENT-TYPE": "application/json", "HOST": "localhost"})
        assert d1 == d3

        assert d1 != {"content-type": "text/html", "host": "localhost"}
        assert d1 != {"different-key": "val", "host": "localhost"}
        assert d1 != 42

    def test_copy_and_deepcopy(self):
        d = CaseInsensitiveDict({"Content-Type": "application/json", "nested": {"a": 1}})
        copied = d.copy()
        assert copied == d
        assert isinstance(copied, CaseInsensitiveDict)
        assert copied["content-type"] == "application/json"

        copied_std = copy.copy(d)
        assert copied_std == d

        deep = copy.deepcopy(d)
        assert deep == d
        assert isinstance(deep, CaseInsensitiveDict)
        assert deep["nested"] is not d["nested"]


class TestDeepCaseInsensitiveDict:
    def test_deep_conversion(self):
        d = DeepCaseInsensitiveDict(
            {
                "Headers": {"Content-Type": "application/json"},
                "Config": {"API_KEY": "secret"},
            }
        )
        assert isinstance(d.headers, DeepCaseInsensitiveDict)
        assert isinstance(d.config, DeepCaseInsensitiveDict)
        assert d.headers.content_type == "application/json"
        assert d.headers["content-type"] == "application/json"
        assert d.config.api_key == "secret"

    def test_deep_assignment(self):
        d = DeepCaseInsensitiveDict()
        d.headers = {"Content-Type": "text/html"}
        assert isinstance(d.headers, DeepCaseInsensitiveDict)
        assert d.headers.content_type == "text/html"

        already_deep = DeepCaseInsensitiveDict({"A": "B"})
        d.sub = already_deep
        assert d.sub.a == "B"


class TestAttributeDict:
    def test_attribute_dict(self):
        d = AttributeDict({"a": 1, "b": 2})
        assert d.a == 1
        assert d.b == 2
        d.c = 3
        assert d["c"] == 3
        with pytest.raises(AttributeError):
            _ = d.missing

    def test_deep_attribute_dict(self):
        d = DeepAttributeDict({"a": {"b": 2}})
        assert isinstance(d.a, DeepAttributeDict)
        assert d.a.b == 2


class TestBorgDict:
    def test_borg_dict(self):
        d1 = BorgDict(a=1, b=2)
        d2 = BorgDict()
        assert d2["a"] == 1
        assert d2["b"] == 2
        assert "a" in d2
        assert len(d2) == 2
        assert list(d2.keys()) == ["a", "b"]
        assert list(d2) == ["a", "b"]
        assert repr(d1) == str(d1)

        d1["c"] = 3
        assert d2["c"] == 3
        assert d2.pop("c") == 3

        del d1["a"]
        assert "a" not in d2


class TestJSONAttributeDict:
    def test_json_attribute_dict(self, tmp_path):
        data = {"host": "localhost", "port": 8080}
        d = JSONAttributeDict(json.dumps(data))
        assert d.host == "localhost"
        assert d.port == 8080
        assert "localhost" in str(d)
        assert "localhost" in repr(d)

        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps(data))
        df = JSONAttributeDict(str(json_file))
        assert df.host == "localhost"

        with pytest.raises(ValueError):
            JSONAttributeDict("invalid json string that is not a file")
