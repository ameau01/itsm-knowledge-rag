"""The ContextualPrecision reference builder (pure)."""

from __future__ import annotations

from evaluation.common.queries import Query
from evaluation.deepeval.expected_output import build_expected_output


def test_single_source_includes_cause_narrative_error():
    q = Query("q", "t", "simple", ["AIT/x"], ["AIT"], [], None,
              source_tickets=["INC-AIT-0001"], error_string="HTTP 504")
    out = build_expected_output(q, {"INC-AIT-0001": "token expired"})
    assert "Correct root cause: AIT/x" in out
    assert "token expired" in out
    assert "HTTP 504" in out
    assert "spans" not in out  # single source → no multi-cause banner


def test_synthesis_concatenates_three_narratives():
    q = Query("q", "t", "simple", ["AIT/x"], ["AIT"], [], None,
              source_tickets=["T1", "T2", "T3"])
    out = build_expected_output(q, {"T1": "n1", "T2": "n2", "T3": "n3"})
    assert "spans 3 related causes" in out
    assert all(n in out for n in ("n1", "n2", "n3"))


def test_excludes_intent_authoring_metadata():
    q = Query("q", "t", "simple", ["AIT/x"], ["AIT"], [], "diagnosis",
              source_tickets=["T1"])
    out = build_expected_output(q, {"T1": "n1"})
    assert "diagnosis" not in out  # intent must not prime the judge
