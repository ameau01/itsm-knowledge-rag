"""
Unit tests for the serve-time relevance gate (src/retrieval/relevance.py).

No model, no Qdrant. Stub arms return fixed points so the gate logic is tested in isolation:
the hybrid ranking sets the order, the dense cosine sets which sections survive the floor.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

from evaluation.common.contracts import RetrievedPoint  # noqa: E402
from retrieval.relevance import relevant_keys            # noqa: E402


class _Arm:
    """Minimal retriever stub: returns its fixed points, honoring k."""

    def __init__(self, points):
        self._points = points

    def retrieve_points(self, query, k):
        return self._points[:k]


def _arms(hybrid_points, dense_points):
    return {"hybrid": _Arm(hybrid_points), "dense": _Arm(dense_points)}


def test_gate_keeps_order_and_drops_below_floor():
    # Hybrid sets the order. Dense cosine decides survival. T2 is below the floor.
    hybrid = [
        RetrievedPoint("T1", "description", 0.0),
        RetrievedPoint("T2", "resolution", 0.0),
        RetrievedPoint("T3", "diagnostics", 0.0),
    ]
    dense = [
        RetrievedPoint("T1", "description", 0.80),
        RetrievedPoint("T3", "diagnostics", 0.55),
        RetrievedPoint("T2", "resolution", 0.40),  # below 0.50
    ]
    keys = relevant_keys(_arms(hybrid, dense), object(), pool=10, floor=0.50)
    assert keys == [("T1", "description"), ("T3", "diagnostics")]


def test_gate_can_return_empty():
    hybrid = [RetrievedPoint("T1", "description", 0.0)]
    dense = [RetrievedPoint("T1", "description", 0.10)]
    assert relevant_keys(_arms(hybrid, dense), object(), pool=10, floor=0.50) == []


def test_missing_dense_score_treated_as_zero():
    # A section ranked by hybrid but absent from the dense pool fails the floor.
    hybrid = [RetrievedPoint("T9", "correspondence", 0.0)]
    dense = []
    assert relevant_keys(_arms(hybrid, dense), object(), pool=10, floor=0.50) == []


def test_default_floor_comes_from_settings():
    from config import settings

    hybrid = [RetrievedPoint("T1", "description", 0.0)]
    above = settings.cosine_relevance_floor + 0.01
    below = settings.cosine_relevance_floor - 0.01
    assert relevant_keys(_arms(hybrid, [RetrievedPoint("T1", "description", above)]),
                         object(), pool=10) == [("T1", "description")]
    assert relevant_keys(_arms(hybrid, [RetrievedPoint("T1", "description", below)]),
                         object(), pool=10) == []
