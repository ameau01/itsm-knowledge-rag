"""Golden-value tests for candidate-set (complex / multi-label) metrics."""

from __future__ import annotations

import pytest

from evaluation.label_based import metrics_set as ms


def test_candidate_set_basic():
    pred = {"A", "B"}
    expected = {"A", "B", "C"}
    assert ms.candidate_set_precision(pred, expected) == pytest.approx(1.0)
    assert ms.candidate_set_recall(pred, expected) == pytest.approx(2 / 3)
    assert ms.candidate_set_f1(pred, expected) == pytest.approx(2 * 1.0 * (2 / 3) / (1.0 + 2 / 3))


def test_anchor_hit():
    assert ms.anchor_hit({"A", "B"}, "A") is True
    assert ms.anchor_hit({"A", "B"}, "C") is False
    assert ms.anchor_hit({"A"}, None) is False


def test_set_size_delta_over_hedging():
    # returning 5 when 2 was right → +3 (over-hedge)
    assert ms.set_size_delta({"A", "B", "C", "D", "E"}, {"A", "B"}) == 3
    assert ms.set_size_delta({"A"}, {"A", "B"}) == -1


def test_score_candidate_set_bundle():
    s = ms.score_candidate_set({"A", "B", "C", "D", "E"}, {"A", "B"}, anchor_root_cause="A")
    assert s.precision == pytest.approx(2 / 5)
    assert s.recall == pytest.approx(1.0)
    assert s.anchor_hit is True
    assert s.set_size_delta == 3


def test_empty_prediction_scores_zero():
    assert ms.candidate_set_precision(set(), {"A"}) == 0.0
    assert ms.candidate_set_f1(set(), {"A"}) == 0.0
