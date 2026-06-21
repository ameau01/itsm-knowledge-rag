"""BM25-only arm — sparse keyword scoring over the sparse named vector."""

from __future__ import annotations

from evaluation.common.queries import Query

from .base import BaseRetriever


class SparseRetriever(BaseRetriever):
    name = "bm25"

    def retrieve_points(self, query: Query, k: int):
        return self._to_points(self._ops.search_sparse(self._s.embed_query(query.text), k))
