"""Hybrid retrieval: dense (Arctic) + sparse (BM25) over Qdrant, fused with RRF."""

from __future__ import annotations


def build_arms(*, ops=None, dense=None, sparse=None):
    """Construct the retriever arms over a shared embedder + Qdrant collection.

    Returns {name: retriever} for dense / bm25 / hybrid. Heavy imports are deferred to call
    time so importing this package stays light.
    """
    from .base import BaseRetriever
    from .dense_retriever import DenseRetriever
    from .hybrid_retriever import HybridRetriever
    from .qdrant_ops import QdrantOps
    from .sparse_retriever import SparseRetriever

    if dense is None:
        from .embeddings import DenseEmbedder
        dense = DenseEmbedder()
    if sparse is None:
        from .embeddings import SparseEmbedder
        sparse = SparseEmbedder()
    ops = ops or QdrantOps()

    arms: dict[str, BaseRetriever] = {
        a.name: a for a in (DenseRetriever(ops, dense, sparse),
                            SparseRetriever(ops, dense, sparse),
                            HybridRetriever(ops, dense, sparse))
    }
    return arms
