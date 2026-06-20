"""Contracts: dedupe rollup and the pure L1EvalCase adapter."""

from __future__ import annotations

from evaluation.common.contracts import (
    NO_GENERATION,
    RetrievedPoint,
    build_l1_eval_case,
    dedupe_to_tickets,
)
from evaluation.common.queries import Query


def _q() -> Query:
    return Query("q1", "the query text", "simple", ["AIT/x"], ["AIT"], [], None,
                 source_tickets=["INC-AIT-0001"])


def test_dedupe_preserves_order():
    assert dedupe_to_tickets(["A", "A", "B", "C", "B"]) == ["A", "B", "C"]


def test_build_l1_eval_case_dual_granularity():
    points = [
        RetrievedPoint("INC-AIT-0001", "description", 0.9),
        RetrievedPoint("INC-AIT-0001", "resolution", 0.8),   # same ticket, 2nd section
        RetrievedPoint("INC-AIT-0002", "description", 0.7),
    ]
    texts = ["desc-1", "res-1", "desc-2"]
    case = build_l1_eval_case(_q(), points, texts, "REFERENCE")

    # deterministic side: deduped to distinct parent tickets, order preserved
    assert case.retrieved_ticket_ids == ["INC-AIT-0001", "INC-AIT-0002"]
    # judge side: point-granular, untouched
    assert case.retrieved_texts == ["desc-1", "res-1", "desc-2"]

    ji = case.to_judge_input()
    assert ji.input_text == "the query text"
    assert ji.retrieval_context == ["desc-1", "res-1", "desc-2"]
    assert ji.expected_output == "REFERENCE"


def test_no_generation_is_a_placeholder():
    assert "no generation" in NO_GENERATION.lower()
