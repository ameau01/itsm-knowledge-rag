"""Judge seam — MockJudge plumbing over the JudgeInput case (no LLM)."""

from __future__ import annotations

import pytest

from evaluation.common.contracts import JudgeInput
from evaluation.deepeval.base import (
    CONTEXTUAL_PRECISION,
    CONTEXTUAL_RELEVANCY,
    JUDGE_METRICS,
)

from _mocks import MockJudge


def _case(qid: str = "q1") -> JudgeInput:
    return JudgeInput(query_id=qid, input_text="t", retrieval_context=["c"], expected_output="ref")


def test_mock_judge_returns_seeded_score():
    j = MockJudge({("q1", CONTEXTUAL_PRECISION): 0.88, ("q1", CONTEXTUAL_RELEVANCY): 0.85})
    assert j.score(_case(), CONTEXTUAL_PRECISION).value == pytest.approx(0.88)
    assert j.score(_case(), CONTEXTUAL_RELEVANCY).value == pytest.approx(0.85)


def test_mock_judge_default_for_unknown():
    j = MockJudge({}, default=0.0)
    assert j.score(_case("zzz"), CONTEXTUAL_PRECISION).value == 0.0


def test_contextual_recall_is_not_a_judge_metric():
    # ContextualRecall is intentionally excluded (duplicates deterministic recall@10).
    assert "contextual_recall" not in JUDGE_METRICS
    assert set(JUDGE_METRICS) == {CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY}
