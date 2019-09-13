import pytest

from cafeteria.datastructs.dict import MergingDict, DeepMergingDict


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


class TestDeepMergingDict:
    def test_simple_deep_merge(self, simple_dict, simple_dict_update):
        d = DeepMergingDict(simple_dict)
        d.update(simple_dict_update)
        assert d == {
            "dict": {"one": 1, "two": 2, "nested": {"a": "a", "b": "b"}},
            "list": [1, 2, 3],
        }
