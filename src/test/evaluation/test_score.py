"""
score.py — classic + deepeval scoring cores and the CLI dispatch.
"""

from __future__ import annotations

import sys

import pytest

from evaluation import score
from evaluation.common.contracts import RetrievedPoint
from evaluation.common.relevance import LENIENT, STRICT
from evaluation.deepeval.base import CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY

from _mocks import MockJudge

QID = "q-ait-diag-1"


def _query(simple_queries):
    return next(q for q in simple_queries if q.query_id == QID)


def test_classic_scores_manual_ranking(oracle, simple_queries):
    q = _query(simple_queries)
    strict = sorted(oracle.relevant_tickets(q, STRICT))
    family = sorted(oracle.relevant_tickets(q, LENIENT))
    non = sorted(oracle.all_ticket_ids - set(family))[:2]  # non-relevant at both levels
    ranked = strict[:3] + non                              # 5 returned: 3 relevant, 2 not

    s = score.classic_scores(q, ranked, oracle, k=10)
    # 3 of the 5 returned are relevant (strict AND family, since strict ⊆ family).
    assert s["strict"]["precision"] == pytest.approx(3 / 5)
    assert s["family"]["precision"] == pytest.approx(3 / 5)
    # capped recall: 3 / min(10, n_relevant).
    assert s["strict"]["recall"] == pytest.approx(3 / min(10, len(strict)))
    assert s["family"]["recall"] == pytest.approx(3 / min(10, len(family)))
    assert int(s["strict"]["n_relevant"]) == len(strict)


def test_classic_family_relevant_is_superset_of_strict(oracle, simple_queries):
    q = _query(simple_queries)
    s = score.classic_scores(q, [], oracle, k=10)
    assert s["family"]["n_relevant"] >= s["strict"]["n_relevant"]


def test_deepeval_scores_with_mock_judge(simple_queries):
    q = _query(simple_queries)
    points = [RetrievedPoint("INC-AIT-0032", "description", 1.0)]
    texts = ["expired api token caused 401 then 504 timeouts"]
    judge = MockJudge({
        (QID, CONTEXTUAL_PRECISION): 0.8,
        (QID, CONTEXTUAL_RELEVANCY): 0.6,
    })
    out = score.deepeval_scores(q, points, texts, narratives={}, judge=judge, n_runs=3)
    assert out["contextual_precision"] == pytest.approx(0.8)
    assert out["contextual_relevancy"] == pytest.approx(0.6)
    assert judge.calls == 2 * 3  # two metrics × n_runs


def test_main_no_tickets_uses_live_path(monkeypatch):
    # No --tickets -> live retriever. If the retriever can't be built (deps/Qdrant/index),
    # main() must surface it as one clean SystemExit. Force the failure so the test is
    # deterministic whether or not retrieval deps happen to be installed here.
    def _boom(*a, **k):
        raise RuntimeError("simulated: retrieval backend unavailable")
    monkeypatch.setattr("retrieval.build_arms", _boom)
    monkeypatch.setattr(sys, "argv", ["score", "--mode", "classic", "--query", QID])
    with pytest.raises(SystemExit) as exc:
        score.main()
    assert "Live retrieval unavailable" in str(exc.value)


def test_main_classic_manual_runs(monkeypatch, capsys, oracle, simple_queries):
    q = _query(simple_queries)
    tickets = ",".join(sorted(oracle.relevant_tickets(q, STRICT))[:2])
    monkeypatch.setattr(
        sys, "argv", ["score", "--mode", "classic", "--query", QID, "--tickets", tickets])
    score.main()
    out = capsys.readouterr().out
    assert "Classic evaluation" in out
    assert "strict" in out and "family" in out


def test_main_unknown_query_fails(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["score", "--mode", "classic", "--query", "nope", "--tickets", "INC-X"])
    with pytest.raises(SystemExit) as exc:
        score.main()
    assert "not found" in str(exc.value)
