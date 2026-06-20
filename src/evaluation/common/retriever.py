"""
Retriever Protocol + the result type the metrics consume.

The Protocol is the seam between the evaluation method and the IR stack. The real arms —
dense-only, BM25-only, hybrid (RRF); reranker deferred — will each implement `rank()`.

`rank()` takes the whole `Query` (not just text) so a mock can look up the right answer by
id; a real retriever simply ignores everything but `query.text`. Mock retrievers (for tests)
live in src/test/evaluation/_mocks.py — they are not part of the IR stack.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .queries import Query


@dataclass(frozen=True)
class RetrievedTicket:
    ticket_id: str
    score: float


@runtime_checkable
class Retriever(Protocol):
    name: str

    def rank(self, query: Query, k: int) -> list[RetrievedTicket]: ...


def ticket_ids(results: Sequence[RetrievedTicket]) -> list[str]:
    """Project a ranking down to its ordered ticket-ids (what metrics consume)."""
    return [r.ticket_id for r in results]
