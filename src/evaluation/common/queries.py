"""
Query-set loading and typing.

Loads the frozen retrieval query files (simple / complex / abstention) into typed
`Query` records. Handles the schema's polymorphic ground-truth fields:
`expected_root_cause` and `expected_family` may be a string (simple), a list
(complex, multi-label), or null (abstention).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def _as_id_list(value: str | list[str] | None) -> list[str]:
    """Normalize a string | list | null ground-truth field to a list of ids."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


@dataclass(frozen=True)
class Query:
    query_id: str
    text: str
    category: str  # 'simple' | 'complex' | 'abstention'
    expected_root_cause: list[str]  # normalized to a list (0 ids for abstention)
    expected_family: list[str]
    expected_ticket_set: list[str]  # synthesis queries; else []
    intent: str | None
    source_tickets: list[str] = field(default_factory=list)
    anchor_root_cause: str | None = None
    error_string: str | None = None  # observed error signature (answer content for the judge)

    @property
    def is_abstention(self) -> bool:
        return self.category == "abstention"

    @property
    def is_multi_label(self) -> bool:
        return len(self.expected_root_cause) > 1


def _query_from_raw(raw: dict) -> Query:
    meta = raw.get("metadata", {}) or {}
    return Query(
        query_id=raw["query_id"],
        text=raw["query"],
        category=raw.get("category", ""),
        expected_root_cause=_as_id_list(raw.get("expected_root_cause")),
        expected_family=_as_id_list(raw.get("expected_family")),
        expected_ticket_set=list(raw.get("expected_ticket_set", []) or []),
        intent=meta.get("intent"),
        source_tickets=list(meta.get("source_tickets", []) or []),
        anchor_root_cause=meta.get("anchor_root_cause"),
        error_string=meta.get("error_string"),
    )


def load_queries(path: str | Path) -> list[Query]:
    """Load a query file (the schema wraps the list under a 'queries' key)."""
    data = json.loads(Path(path).read_text())
    raw_queries = data["queries"] if isinstance(data, dict) else data
    return [_query_from_raw(q) for q in raw_queries]
