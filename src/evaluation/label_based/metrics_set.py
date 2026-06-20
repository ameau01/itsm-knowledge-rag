"""
Candidate-set metrics for complex (multi-label) queries — Axis 3.

A complex query has 2–3 valid root causes. The system returns a *set* of candidate
root causes (derived from its retrieved tickets). These functions score that predicted
set against the expected set. All pure functions over sets of root-cause ids.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateSetScore:
    precision: float
    recall: float
    f1: float
    anchor_hit: bool
    set_size_delta: int  # |predicted| - |expected|; >0 = over-hedging


def candidate_set_precision(predicted: Iterable[str], expected: Iterable[str]) -> float:
    pred, exp = set(predicted), set(expected)
    if not pred:
        return 0.0
    return len(pred & exp) / len(pred)


def candidate_set_recall(predicted: Iterable[str], expected: Iterable[str]) -> float:
    pred, exp = set(predicted), set(expected)
    if not exp:
        return 0.0
    return len(pred & exp) / len(exp)


def candidate_set_f1(predicted: Iterable[str], expected: Iterable[str]) -> float:
    p = candidate_set_precision(predicted, expected)
    r = candidate_set_recall(predicted, expected)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def anchor_hit(predicted: Iterable[str], anchor_root_cause: str | None) -> bool:
    """Did the primary intended cause survive into the returned set?"""
    if anchor_root_cause is None:
        return False
    return anchor_root_cause in set(predicted)


def set_size_delta(predicted: Iterable[str], expected: Iterable[str]) -> int:
    """Over-hedging signal: returning 5 candidates when 2 was right scores +3."""
    return len(set(predicted)) - len(set(expected))


def score_candidate_set(
    predicted: Iterable[str],
    expected: Iterable[str],
    anchor_root_cause: str | None = None,
) -> CandidateSetScore:
    pred = set(predicted)
    return CandidateSetScore(
        precision=candidate_set_precision(pred, expected),
        recall=candidate_set_recall(pred, expected),
        f1=candidate_set_f1(pred, expected),
        anchor_hit=anchor_hit(pred, anchor_root_cause),
        set_size_delta=set_size_delta(pred, expected),
    )
