from __future__ import annotations

import logging
from collections.abc import Hashable
from collections.abc import Mapping
from typing import Any
from typing import TypeVar

logger = logging.getLogger(__name__)

D = TypeVar("D")

__all__ = ["get_by_path"]


def get_by_path(d: Mapping[Any, Any], *path: Hashable, default: D | None = None) -> Any | D | None:
    """
    Given a nested dict of dicts, traverse a given path and return the result or the default if it is not found.
    This is used as a replacement for the pattern
    >>> d.get("a", {}).get("b", {}).get("c", {}).get("d", 1)
    with
    >>> get_by_path(d, "a", "b", "c", "d", default=1)

    Does not traverse lists. Should be dict all the way down.
    """
    if len(path) == 0:
        raise ValueError("No path given")

    head, *tail = path
    logger.debug("head: %s, tail: %s", head, tail)

    if not tail:
        return d.get(head, default)

    try:
        return get_by_path(d[head], *tail, default=default)
    except (KeyError, TypeError):
        return default
