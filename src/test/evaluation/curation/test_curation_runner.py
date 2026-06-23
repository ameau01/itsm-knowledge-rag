"""Runner plumbing — arms x pages x metrics x runs, aggregation, singleton exclusion."""

from __future__ import annotations

from evaluation.curation.contracts import VARIATION, Candidate, JudgeScore, PageMeta
from evaluation.curation.runner import aggregate_curation, run_curation_eval

_U = {"title": "T", "symptoms": "S", "cause": "C", "variations": "V", "reporting": "R"}
_CTX = {"title": ["x"], "symptoms": ["x"], "cause": ["x"], "variations": ["x"]}
_POOL = {"title": ["p"], "symptoms": ["p"], "cause": ["p"], "variations": ["p"]}


class MockCurationJudge:
    """Pre-seeded scores by (root_cause_id, metric); counts calls."""

    name = "mock"

    def __init__(self, scores=None, default=0.5):
        self._scores = scores or {}
        self._default = default
        self.calls = 0

    def score(self, case):
        self.calls += 1
        return JudgeScore(case.metric, self._scores.get((case.root_cause_id, case.metric), self._default))


def _cand(arm, rc):
    return Candidate(arm=arm, root_cause_id=rc, family="VDA", curation=_U, context=_CTX)


def _meta(rc, n):
    return PageMeta(root_cause_id=rc, n_members=n, evidence_pool=_POOL)


def _setup():
    multi, single = "VDA/multi", "VDA/single"
    cands = {
        "gold": [_cand("gold", multi), _cand("gold", single)],
        "other": [_cand("other", multi), _cand("other", single)],
    }
    meta = {multi: _meta(multi, 3), single: _meta(single, 1)}
    return cands, meta


def test_result_count_and_runs():
    cands, meta = _setup()
    judge = MockCurationJudge()
    results = run_curation_eval(cands, meta, judge, n_runs=3)
    # multi page: 4 faithfulness + relevancy + summarization + variation = 7 cases
    # single page: 4 faithfulness + relevancy + summarization        = 6 cases
    # per arm: (7 + 6) * 3 runs = 39 ; two arms = 78
    assert len(results) == 78
    assert judge.calls == 78
    assert {r.run for r in results} == {0, 1, 2}


def test_variation_only_on_multi_ticket():
    cands, meta = _setup()
    results = run_curation_eval(cands, meta, MockCurationJudge(), n_runs=3)
    var = [r for r in results if r.metric == VARIATION]
    assert {r.root_cause_id for r in var} == {"VDA/multi"}   # singleton excluded
    assert len(var) == 2 * 3                                  # 2 arms x 3 runs, multi only


def test_aggregate_mean_and_spread():
    cands, meta = _setup()
    scores = {("VDA/multi", "answer_relevancy"): 1.0, ("VDA/single", "answer_relevancy"): 0.0}
    results = run_curation_eval(cands, meta, MockCurationJudge(scores, default=0.5), n_runs=3)
    agg = aggregate_curation(results)
    mean, _ = agg[("gold", "answer_relevancy")]
    assert mean == 0.5                       # mean of 1.0 (multi) and 0.0 (single)
    fmean, fspread = agg[("gold", "faithfulness:symptoms")]
    assert fmean == 0.5 and fspread == 0.0   # constant default -> zero spread
