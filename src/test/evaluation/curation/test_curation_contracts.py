"""Curation case builder — pure, no DB. Asserts the split-reference wiring and singleton rule."""

from __future__ import annotations

from evaluation.curation.contracts import (
    ANSWER_RELEVANCY,
    SUMMARIZATION,
    VARIATION,
    Candidate,
    build_curation_cases,
    faithfulness_metric,
)

_U = {
    "title": "GlobalProtect drops after MFA",
    "symptoms": "VPN disconnects ~30s after Okta MFA succeeds.",
    "cause": "Device certificate expired.",
    "variations": "Some users see a cert prompt; others a silent drop.",
    "reporting": "Contact IT and mention certificate.",
}
# Per-arm context: what THIS arm fed its model, per field.
_CTX = {
    "title": ["t-ctx"],
    "symptoms": ["sym-ctx-a", "sym-ctx-b"],
    "cause": ["cause-ctx"],
    "variations": ["var-ctx"],
}
# Full evidence pool (all members, uncapped) for coverage metrics.
_POOL = {
    "title": ["pool-all"],
    "symptoms": ["pool-sym-1", "pool-sym-2", "pool-sym-3"],
    "cause": ["pool-cause"],
    "variations": ["pool-var-1", "pool-var-2"],
}


def _cand(arm="gold"):
    return Candidate(arm=arm, root_cause_id="VDA/x", family="VDA", curation=_U, context=_CTX)


def test_faithfulness_uses_per_arm_context_not_pool():
    cases = {c.metric: c for c in build_curation_cases(_cand(), _POOL, multi_ticket=True)}
    fc = cases[faithfulness_metric("symptoms")]
    assert fc.actual_output == _U["symptoms"]
    assert fc.retrieval_context == _CTX["symptoms"]      # per-arm context
    assert fc.retrieval_context != _POOL["symptoms"]     # NOT the full pool


def test_reporting_is_not_faithfulness_checked():
    metrics = {c.metric for c in build_curation_cases(_cand(), _POOL, multi_ticket=True)}
    assert faithfulness_metric("reporting") not in metrics
    # the four generated fields are checked
    for f in ("title", "symptoms", "cause", "variations"):
        assert faithfulness_metric(f) in metrics


def test_summarization_source_is_full_pool():
    cases = {c.metric: c for c in build_curation_cases(_cand(), _POOL, multi_ticket=True)}
    summ = cases[SUMMARIZATION]
    # body = symptoms+cause+variations; source doc (input) = deduped union of the pool
    assert _U["symptoms"] in summ.actual_output and _U["cause"] in summ.actual_output
    assert "pool-sym-1" in summ.input_text and "pool-var-2" in summ.input_text


def test_variation_excluded_for_singleton():
    multi = {c.metric for c in build_curation_cases(_cand(), _POOL, multi_ticket=True)}
    single = {c.metric for c in build_curation_cases(_cand(), _POOL, multi_ticket=False)}
    assert VARIATION in multi
    assert VARIATION not in single
    assert ANSWER_RELEVANCY in single  # relevancy still runs on singletons


def test_variation_judged_against_pool():
    cases = {c.metric: c for c in build_curation_cases(_cand(), _POOL, multi_ticket=True)}
    var = cases[VARIATION]
    assert var.retrieval_context == _POOL["variations"]
    assert _U["variations"] in var.actual_output
