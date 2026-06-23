"""Report rendering — table shape + singleton accounting (no judge)."""

from __future__ import annotations

from evaluation.curation.contracts import ANSWER_RELEVANCY, VARIATION, PageMeta, faithfulness_metric
from evaluation.curation.report import format_report

_META = {
    "VDA/multi": PageMeta("VDA/multi", n_members=53, evidence_pool={}),
    "VDA/single": PageMeta("VDA/single", n_members=1, evidence_pool={}),
}
_AGG = {
    ("gold", faithfulness_metric("symptoms")): (0.97, 0.01),
    ("gold", ANSWER_RELEVANCY): (0.90, 0.00),
    ("gold", VARIATION): (0.80, 0.05),
    ("react", faithfulness_metric("symptoms")): (0.88, 0.04),
}


def test_report_lists_arms_metrics_and_singletons():
    out = format_report(
        _AGG, arms=["gold", "react"], page_meta=_META, judge_name="deepeval-curation:gpt", n_runs=3,
    )
    assert "gold" in out and "react" in out
    assert faithfulness_metric("symptoms") in out and VARIATION in out
    assert "0.970 ±0.010" in out and "0.880 ±0.040" in out
    assert "1 singleton" in out and "VDA/single" in out      # singleton accounted + named
    assert "—" in out                                         # react has no variation cell
