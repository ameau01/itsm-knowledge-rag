"""Abstention calibration tests, including the no-leak property."""

from __future__ import annotations

import numpy as np
import pytest

from evaluation.label_based.abstention import (
    ScoredQuery,
    calibrate_floor,
    evaluate_abstention,
    should_abstain,
)


def test_calibrate_floor_percentile():
    scores = list(range(1, 11))  # 1..10
    assert calibrate_floor(scores, 10) == pytest.approx(np.percentile(scores, 10))
    assert calibrate_floor(scores, 10) == pytest.approx(1.9)


def test_calibrate_floor_uses_only_in_corpus_scores():
    """No-leak property: the floor is a pure function of the in-corpus scores. There is
    no parameter through which out-of-corpus / abstention labels could influence it."""
    in_corpus = [0.70, 0.72, 0.80, 0.85, 0.90]
    floor_a = calibrate_floor(in_corpus, 5)
    floor_b = calibrate_floor(in_corpus, 5)  # any test set could exist; floor cannot move
    assert floor_a == floor_b == pytest.approx(np.percentile(in_corpus, 5))


def test_calibrate_floor_rejects_empty():
    with pytest.raises(ValueError):
        calibrate_floor([], 5)


def test_should_abstain():
    assert should_abstain(0.1, 0.5) is True
    assert should_abstain(0.6, 0.5) is False


def test_evaluate_abstention_clean_separation():
    floor = 0.5
    scored = [
        ScoredQuery(0.8, should_abstain=False),  # answerable, clears floor
        ScoredQuery(0.9, should_abstain=False),
        ScoredQuery(0.2, should_abstain=True),   # out-of-corpus, below floor
        ScoredQuery(0.1, should_abstain=True),
    ]
    rep = evaluate_abstention(scored, floor)
    assert rep.abstention_accuracy == pytest.approx(1.0)
    assert rep.false_abstention_rate == pytest.approx(0.0)
    assert rep.n_should_abstain == 2
    assert rep.n_answerable == 2
    assert sorted(rep.in_corpus_scores) == [0.8, 0.9]
    assert sorted(rep.out_of_corpus_scores) == [0.1, 0.2]


def test_evaluate_abstention_counts_false_abstention():
    floor = 0.5
    scored = [
        ScoredQuery(0.1, should_abstain=False),  # answerable but below floor → wrong
        ScoredQuery(0.8, should_abstain=False),
        ScoredQuery(0.2, should_abstain=True),
    ]
    rep = evaluate_abstention(scored, floor)
    assert rep.false_abstention_rate == pytest.approx(0.5)
    assert rep.abstention_accuracy == pytest.approx(1.0)
