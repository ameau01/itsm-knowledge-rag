"""Hybrid arm — dense + sparse fused with Reciprocal Rank Fusion (the serving default)."""

from __future__ import annotations

from evaluation.common.queries import Query

from .base import BaseRetriever


class HybridRetriever(BaseRetriever):
    name = "hybrid"

    def retrieve_points(self, query: Query, k: int, query_filter=None):
        return self._to_points(self._ops.search_hybrid(
            self._d.embed_query(query.text), self._s.embed_query(query.text),
            k, query_filter))
