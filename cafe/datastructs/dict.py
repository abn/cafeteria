from copy import deepcopy
from json import loads, load, dumps

from os.path import isfile

from cafe.patterns.borg import Borg
from cafe.utilities import is_str


class AttributeDict(dict):
    """
    A dictionary implementation that allows for all keys to be used as an
    attribute. In this implementation we do proper get/setattr override here,
    no self.__dict__ mambo jumbo.
    """

    def __init__(self, *args, **kwargs):
        super(AttributeDict, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError(
            "Could not get attr: '{}' from '{}'".format(item, self)
        )

    def __setattr__(self, key, value):
        self[key] = value


class DeepAttributeDict(AttributeDict):
    """
    A DeepAttributeDict is an AttributeDict of which dict objects at all depths
    are converted to DeepAttributeDict.
    """

    def __init__(self, *args, **kwargs):
        super(DeepAttributeDict, self).__init__(*args, **kwargs)
        self._deep_init()

    def _deep_init(self):
        for key, value in self.items():
            if isinstance(value, dict) and \
                    not isinstance(value, AttributeDict):
                self[key] = DeepAttributeDict(value)


class MergingDict(AttributeDict):
    """
    A MergingDict is an AttributeDict whose attribute/item values are always
    merged if the rvalue implements an update or append method. If the rvalue
    is not merge-able, it is simply replaced.
    """

    def replace(self, key, value):
        """
        Convenience method provided as a way to replace a value mapped by a
        key.This is required since a MergingDict always merges via assignment
        of item/attribute.

        :param key: Attribute name or item key to replace rvalue for.
        :type key: object
        :param value: The new value to assign.
        :type value: object
        :return:
        """
        super(MergingDict, self).__setitem__(key, value)

    def update(self, other=None, **kwargs):
        """
        A special update method to handle merging of dict objects. For all
        other iterable objects, we use the parent class update method. For
        other objects, we simply make use of the internal merging logic.

        :param other: An iterable object.
        :type other: dict or object
        :param kwargs: key/value pairs to update.
        :rtype: None
        """
        if other is not None:
            if isinstance(other, dict):
                for key in other:
                    self[key] = other[key]
            else:
                # noinspection PyTypeChecker
                super(MergingDict, self).update(other)

        for key in kwargs:
            self._merge(key, kwargs[key])

    def _merge_method(self, key):
        """
        Identify a merge compatible method available in self[key]. Currently we
        support 'update' and 'append'.

        :param key: Attribute name or item key
        :return: Method name usable to merge a value into the instance mapped
                by key
        :rtype: str
        """
        if key in self:
            for method in ['update', 'append']:
                if hasattr(self[key], method):
                    return method
        return None

    def _merge(self, key, value):
        """
        Internal merge logic implementation to allow merging of values when
        setting attributes/items.

        :param key: Attribute name or item key
        :type key: str
        :param value: Value to set attribute/item as.
        :type value: object
        :rtype: None
        """
        method = self._merge_method(key)
        if method is not None:
            # strings are special, update methods like set.update looks for
            # iterables
            if method is 'update' and is_str(value):
                value = [value]
            if method is 'append' \
                    and isinstance(self[key], list) \
                    and isinstance(value, list):
                # if rvalue is a list and given object is a list, we expect all
                # values to be appended
                method = 'extend'
            getattr(self[key], method)(value)
        else:
            super(MergingDict, self).__setitem__(key, value)

    def __setitem__(self, key, value):
        self._merge(key, value)

    def __setattr__(self, key, value):
        self._merge(key, value)


class DeepMergingDict(MergingDict):
    """
    A DeepMergingDict is a MergingDict of which dict objects at all depths are
    converted to DeepMergingDicts.
    """

    def __init__(self, *args, **kwargs):
        super(DeepMergingDict, self).__init__(*args, **kwargs)
        self._deep_init()

    @staticmethod
    def _should_cast(value):
        return isinstance(value, dict) and not isinstance(value, MergingDict)

    def _deep_init(self):
        for key, value in self.items():
            if self._should_cast(value):
                self.replace(key, DeepMergingDict(value))

    def replace(self, key, value):
        if self._should_cast(value):
            value = DeepMergingDict(value)
        super(DeepMergingDict, self).replace(key, value)

    def update(self, other=None, **kwargs):
        if self._should_cast(other):
            other = DeepMergingDict(other)
        super(DeepMergingDict, self).update(other, **kwargs)


class BorgDict(Borg, dict):
    """
    An dict implementing the Borg Pattern. This can be extended via
    inheritance. In this implementation the dict itself is not used. All
    actions are mapped to the Borg shared state.
    """

    def __init__(self, *args, **kwargs):
        super(BorgDict, self).__init__()
        self.update(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __delitem__(self, key):
        delattr(self, key)

    def __repr__(self):
        return self.__dict__.__repr__()

    def __str__(self):
        return self.__dict__.__str__()

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __contains__(self, k):
        return self.__dict__.__contains__(k)

    def keys(self):
        return self.__dict__.keys()


class JSONAttributeDict(AttributeDict):
    """
    :type source: str or dict or cafe.datastructs.dict.JSONAttributeDict
    """

    def __init__(self, source):
        super(JSONAttributeDict, self).__init__()

        try:
            self.update(loads(source) if is_str(source) else deepcopy(source))
        except ValueError:
            if isfile(source):
                with open(source) as sf:
                    self.update(load(sf))
            else:
                raise ValueError(source)

    @property
    def pretty(self):
        return dumps(self, indent=2)

    def __str__(self):
        return self.pretty

    def __repr__(self):
        return self.pretty
