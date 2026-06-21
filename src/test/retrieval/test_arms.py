"""
Vector arms over an in-memory Qdrant with a deterministic fake embedder.

No model downloads, no live Qdrant — exercises qdrant_ops (collection, upsert, dense/sparse/
hybrid search) and the dense/bm25/hybrid arms (incl. ticket-level dedup).
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

import pytest

pytest.importorskip("qdrant_client")  # needs `uv sync --group retrieval`

from qdrant_client import QdrantClient, models

from evaluation.common.queries import Query
from retrieval.dense_retriever import DenseRetriever
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.qdrant_ops import DENSE, SPARSE, QdrantOps
from retrieval.sparse_retriever import SparseRetriever


class FakeDense:
    dim = 4

    def _vec(self, text: str):
        t = text.lower()
        if "vpn" in t:
            return [1.0, 0.0, 0.0, 0.0]
        if "dns" in t:
            return [0.0, 1.0, 0.0, 0.0]
        return [0.0, 0.0, 1.0, 0.0]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class FakeSparse:
    _IDX = {"vpn": 1, "dns": 2, "timeout": 3}

    def _vec(self, text: str):
        idx = [i for w, i in self._IDX.items() if w in text.lower()] or [99]
        return models.SparseVector(indices=idx, values=[1.0] * len(idx))

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


DOCS = [
    ("T1", "description", "vpn disconnect after mfa"),
    ("T1", "resolution", "vpn tunnel fix"),
    ("T2", "description", "dns resolution failure"),
]


def _ops_with_docs():
    ops = QdrantOps(collection="test", client=QdrantClient(":memory:"))
    ops.ensure_collection(dim=FakeDense.dim)
    d, s = FakeDense(), FakeSparse()
    dv = d.embed_documents([x[2] for x in DOCS])
    sv = s.embed_documents([x[2] for x in DOCS])
    pts = [
        models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{tid}:{sec}")),
            vector={DENSE: dvec, SPARSE: svec},
            payload={"ticket_id": tid, "section_name": sec})
        for (tid, sec, _), dvec, svec in zip(DOCS, dv, sv)
    ]
    ops.upsert(pts)
    return ops, d, s


_Q = Query("q", "vpn issue", "simple", ["X"], ["F"], [], None)


def test_collection_and_count():
    ops, _, _ = _ops_with_docs()
    assert ops.count() == 3


def test_each_arm_ranks_and_dedupes():
    ops, d, s = _ops_with_docs()
    for arm_cls in (DenseRetriever, SparseRetriever, HybridRetriever):
        arm = arm_cls(ops, d, s)
        ranked = [t.ticket_id for t in arm.rank(_Q, 5)]
        assert ranked[0] == "T1", arm_cls.name           # vpn query -> T1 first
        assert ranked.count("T1") == 1, arm_cls.name      # two T1 sections collapse to one ticket


def test_retrieve_points_count_is_exact_not_overfetched():
    # retrieve_points(query, n) returns exactly n points (capped by corpus size). The
    # over-fetch needed to fill k tickets after dedup lives in rank(), not here — so every
    # arm hands the judge the same number of contexts and the benchmark stays fair.
    ops, d, s = _ops_with_docs()
    assert len(DenseRetriever(ops, d, s).retrieve_points(_Q, 2)) == 2


def test_points_keep_section_granularity_before_dedup():
    ops, d, s = _ops_with_docs()
    pts = DenseRetriever(ops, d, s).retrieve_points(_Q, 5)
    t1 = [p for p in pts if p.ticket_id == "T1"]
    assert {p.section_name for p in t1} == {"description", "resolution"}  # both sections present


def test_embeddings_module_imports_without_heavy_deps():
    import retrieval.embeddings  # noqa: F401  (top-level import must not need torch/fastembed)
