"""
BaseRetriever — shared scaffolding for the retriever arms.

Each arm overrides `retrieve_points` (point-level, for the judge); `rank` dedupes those to
parent tickets (Retriever Protocol, for the label metrics). Returns the read-only eval
contract types — never redefines them.
"""

from __future__ import annotations

from evaluation.common.contracts import RetrievedPoint
from evaluation.common.queries import Query
from evaluation.common.retriever import RetrievedTicket


class BaseRetriever:
    name = "base"
    # Over-fetch factor for ticket ranking: a ticket has up to 4 sections, so the top-k
    # *points* can collapse to fewer than k *tickets* after dedup. rank() fetches k*_OVER
    # points so the dedup can still fill k tickets. retrieve_points itself stays exact —
    # retrieve_points(query, n) returns n points — so every arm feeds the judge the same
    # number of contexts and the comparison across arms is fair.
    _OVER = 4

    def __init__(self, ops, dense, sparse) -> None:
        self._ops, self._d, self._s = ops, dense, sparse

    def retrieve_points(self, query: Query, k: int) -> list[RetrievedPoint]:
        raise NotImplementedError

    @staticmethod
    def _to_points(raw) -> list[RetrievedPoint]:
        return [RetrievedPoint(p.payload["ticket_id"], p.payload["section_name"], p.score)
                for p in raw]

    def rank(self, query: Query, k: int) -> list[RetrievedTicket]:
        seen: set[str] = set()
        out: list[RetrievedTicket] = []
        for p in self.retrieve_points(query, k * self._OVER):
            if p.ticket_id not in seen:
                seen.add(p.ticket_id)
                out.append(RetrievedTicket(p.ticket_id, p.score))
        return out[:k]
