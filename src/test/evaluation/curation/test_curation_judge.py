"""Judge wiring — pure, offline (no deepeval, no API).

Validates the case -> LLMTestCase mapping with a dict factory, the metric-key resolution,
and the cache (which, unlike L1's, keys on actual_output)."""

from __future__ import annotations

from evaluation.curation.cache import CurationCache
from evaluation.curation.contracts import (
    ANSWER_RELEVANCY,
    FAITHFULNESS,
    SUMMARIZATION,
    VARIATION,
    CurationCase,
    faithfulness_metric,
)
from evaluation.curation.judge import base_metric, build_test_case


def _case(metric, *, ctx=("c1", "c2")):
    return CurationCase(
        case_id=f"rc::{metric}", arm="gold", root_cause_id="VDA/x", metric=metric,
        input_text="SRC", actual_output="OUT", retrieval_context=list(ctx),
    )


def test_base_metric_strips_field():
    assert base_metric(faithfulness_metric("symptoms")) == FAITHFULNESS
    assert base_metric(ANSWER_RELEVANCY) == ANSWER_RELEVANCY


def test_faithfulness_case_includes_retrieval_context():
    tc = build_test_case(_case(faithfulness_metric("symptoms")), dict)
    assert tc == {"input": "SRC", "actual_output": "OUT", "retrieval_context": ["c1", "c2"]}


def test_relevancy_and_summarization_omit_retrieval_context():
    for metric in (ANSWER_RELEVANCY, SUMMARIZATION):
        tc = build_test_case(_case(metric), dict)
        assert "retrieval_context" not in tc
        assert tc["input"] == "SRC" and tc["actual_output"] == "OUT"


def test_variation_case_includes_context():
    tc = build_test_case(_case(VARIATION), dict)
    assert tc["retrieval_context"] == ["c1", "c2"]


def test_cache_key_depends_on_actual_output(tmp_path):
    cache = CurationCache(tmp_path / "c.json")
    a = _case(ANSWER_RELEVANCY)
    b = CurationCase(**{**a.__dict__, "actual_output": "DIFFERENT"})
    ka, kb = cache.key("judge", a), cache.key("judge", b)
    assert ka != kb                      # generation-aware: different output -> different key
    cache.put(ka, 0.9)
    assert cache.get(ka) == 0.9 and cache.get(kb) is None


def test_cache_roundtrip_persists(tmp_path):
    p = tmp_path / "c.json"
    k = CurationCache(p).key("judge", _case(SUMMARIZATION))
    CurationCache(p).put(k, 0.42)
    assert CurationCache(p).get(k) == 0.42   # re-opened from disk
