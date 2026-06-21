"""Dense-only arm — embedding similarity (Arctic) over the dense named vector."""

from __future__ import annotations

from evaluation.common.queries import Query

from .base import BaseRetriever


class DenseRetriever(BaseRetriever):
    name = "dense"

    def retrieve_points(self, query: Query, k: int):
        return self._to_points(self._ops.search_dense(self._d.embed_query(query.text), k))
