"""Golden-value tests for the rank metrics — hand-computed expected numbers."""

from __future__ import annotations

import math

import pytest

from evaluation.label_based import metrics_rank as mr

# A small ranking. R = relevant, x = not. relevant cluster has 10 members total.
RANKED = ["R1", "x1", "R2", "x2", "R3", "x3", "x4", "x5", "x6", "x7"]
RELEVANT_10 = {f"R{i}" for i in range(1, 11)}  # only R1..R3 are in RANKED


def test_recall_at_k_capped_denominator():
    # top-5 has R1,R2,R3 = 3 hits; denom = min(5, 10) = 5
    assert mr.recall_at_k(RANKED, RELEVANT_10, 5, n_relevant=10) == pytest.approx(3 / 5)


def test_recall_caps_against_k_not_cluster_size():
    # The denominator bug guard: 10 hits against a 53-cluster at k=10 must be 1.0,
    # NOT 10/53.
    ranked = [f"R{i}" for i in range(1, 11)]
    relevant = {f"R{i}" for i in range(1, 54)}  # 53-member cluster
    assert mr.recall_at_k(ranked, relevant, 10, n_relevant=53) == pytest.approx(1.0)


def test_recall_zero_when_nothing_relevant():
    assert mr.recall_at_k(RANKED, set(), 5) == 0.0


def test_precision_at_k():
    # top-5 of RANKED = [R1,x1,R2,x2,R3] → 3 relevant of 5 slots.
    assert mr.precision_at_k(RANKED, RELEVANT_10, 5) == pytest.approx(3 / 5)
    # short manual ranking graded over what it returned (2 of 2), not /k.
    assert mr.precision_at_k(["R1", "R2"], RELEVANT_10, 10) == pytest.approx(1.0)
    # one relevant, one not, in a 2-result list.
    assert mr.precision_at_k(["R1", "x1"], RELEVANT_10, 10) == pytest.approx(0.5)
    assert mr.precision_at_k([], RELEVANT_10, 10) == 0.0


def test_ndcg_at_k_handcomputed():
    # ranked top-3 = [R, x, R], relevant cluster size 2.
    ranked = ["R1", "x1", "R2"]
    relevant = {"R1", "R2"}
    dcg = 1 / math.log2(2) + 0 + 1 / math.log2(4)        # 1.0 + 0.5
    idcg = 1 / math.log2(2) + 1 / math.log2(3)           # ideal: two ones up front
    assert mr.ndcg_at_k(ranked, relevant, 3) == pytest.approx(dcg / idcg)


def test_ndcg_perfect_is_one():
    ranked = ["R1", "R2", "R3"]
    relevant = {"R1", "R2", "R3"}
    assert mr.ndcg_at_k(ranked, relevant, 3) == pytest.approx(1.0)


def test_reciprocal_rank():
    # R1 is first in RANKED → RR = 1/1
    assert mr.reciprocal_rank(RANKED, RELEVANT_10) == pytest.approx(1.0)
    # first relevant at position 3 (1-based) → 1/3
    assert mr.reciprocal_rank(["x0", "x9", "R1", "R2"], RELEVANT_10) == pytest.approx(1 / 3)
    assert mr.reciprocal_rank(["x1", "x2"], RELEVANT_10) == 0.0
