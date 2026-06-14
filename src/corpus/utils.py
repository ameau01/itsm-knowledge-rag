"""
Shared primitive helpers for corpus extraction.

Defined here so any corpus module (extractor, catalog, future modules)
can import them without pulling in the heavier extractor module and
creating a circular dependency.
"""

from __future__ import annotations

from typing import Any


def to_list(val: Any) -> list:  # type: ignore[type-arg]
    """Coerce a value to a plain Python list; returns [] for None."""
    if val is None:
        return []
    if hasattr(val, "tolist"):
        return val.tolist()
    return list(val) if isinstance(val, (list, tuple)) else []


def str_or_empty(val: object) -> str:
    """Coerce a value to str; returns '' for None or float (NaN)."""
    if val is None or isinstance(val, float):
        return ""
    return str(val)
