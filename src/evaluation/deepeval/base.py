"""
Judge seam — the `Judge` Protocol, score type, and metric constants.

The judge is a secondary, qualitative cross-check (never a gate). Per
docs/retrieval-evaluation.md the L1 judge uses ContextualPrecision and
ContextualRelevancy across the four arms; ContextualRecall and Faithfulness are
deliberately excluded (the first duplicates deterministic recall@10; the second needs a
generated output L1 does not have).

The real implementation lives in `deepeval_judge.py`. A `MockJudge` (for tests, no LLM
call) lives in src/test/evaluation/_mocks.py. The judge takes a `JudgeInput` case (so it
never knows about the eval-set schema) and returns a single metric's score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..common.contracts import JudgeInput

CONTEXTUAL_PRECISION = "contextual_precision"
CONTEXTUAL_RELEVANCY = "contextual_relevancy"
JUDGE_METRICS = (CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY)


@dataclass(frozen=True)
class JudgeScore:
    metric: str
    value: float


class Judge(Protocol):
    name: str

    def score(self, case: JudgeInput, metric: str) -> JudgeScore: ...
