"""
Real Qdrant retriever — deferred to the IR build phase (stub).

When wired, it runs dense + BM25 retrieval, fuses with RRF, optionally reranks with a
cross-encoder, and returns ranked `RetrievedPoint`s (one per ticket section). The
deterministic harness consumes a ticket-level rollup of these points
(`dedupe_to_tickets`); the judge path uses them granular with text resolved via
`adapter/corpus.py`. Until the IR stack exists, harness tests run on the mock retrievers
in `common/retriever.py`.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..common.contracts import RetrievedPoint
from ..common.queries import Query


class QdrantRetriever:
    name = "qdrant"

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "QdrantRetriever is wired in the IR build phase. "
            "Use the mock retrievers in evaluation.common.retriever for harness tests."
        )

    def retrieve_points(self, query: Query, k: int) -> Sequence[RetrievedPoint]:
        raise NotImplementedError
