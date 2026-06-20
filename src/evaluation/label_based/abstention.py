"""
Abstention as one-class calibration
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np


def calibrate_floor(in_corpus_scores: Iterable[float], percentile: float) -> float:
    """
    Abstention floor = the `percentile`-th percentile of in-corpus legitimate-match
    top-scores. A percentile of 5.0 means "accept ~5% in-corpus false-abstention".

    Depends ONLY on in-corpus scores — no out-of-corpus / abstention labels enter here.
    """
    scores = np.asarray(list(in_corpus_scores), dtype=float)
    if scores.size == 0:
        raise ValueError("need at least one in-corpus score to calibrate a floor")
    if not 0.0 <= percentile <= 100.0:
        raise ValueError("percentile must be in [0, 100]")
    return float(np.percentile(scores, percentile))


def should_abstain(top_score: float, floor: float) -> bool:
    """Abstain when the best fused score fails to clear the calibrated floor."""
    return top_score < floor


@dataclass(frozen=True)
class AbstentionReport:
    abstention_accuracy: float       # of queries that SHOULD abstain, fraction that did
    false_abstention_rate: float     # of answerable queries, fraction wrongly abstained
    n_should_abstain: int
    n_answerable: int
    in_corpus_scores: list[float]    # recorded for the distribution-separation finding
    out_of_corpus_scores: list[float]


@dataclass(frozen=True)
class ScoredQuery:
    top_score: float
    should_abstain: bool  # ground truth: True for abstention queries, False otherwise


def evaluate_abstention(scored: Sequence[ScoredQuery], floor: float) -> AbstentionReport:
    """
    Apply an already-calibrated floor to a labelled set and report both rates plus the
    two score distributions (in-corpus vs out-of-corpus) for the separation finding.
    """
    correct_abstain = 0
    n_should = 0
    wrong_abstain = 0
    n_answerable = 0
    in_corpus: list[float] = []
    out_corpus: list[float] = []

    for q in scored:
        predicted = should_abstain(q.top_score, floor)
        if q.should_abstain:
            n_should += 1
            out_corpus.append(q.top_score)
            if predicted:
                correct_abstain += 1
        else:
            n_answerable += 1
            in_corpus.append(q.top_score)
            if predicted:
                wrong_abstain += 1

    return AbstentionReport(
        abstention_accuracy=correct_abstain / n_should if n_should else 0.0,
        false_abstention_rate=wrong_abstain / n_answerable if n_answerable else 0.0,
        n_should_abstain=n_should,
        n_answerable=n_answerable,
        in_corpus_scores=in_corpus,
        out_of_corpus_scores=out_corpus,
    )
