"""Four-arm judge runner + aggregation + cache, all via MockJudge (no LLM)."""

from __future__ import annotations

import pytest

from evaluation.common.contracts import RetrievedPoint
from evaluation.common.queries import Query
from evaluation.deepeval.base import CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY
from _mocks import MockJudge
from evaluation.deepeval.cache import JudgeCache
from evaluation.deepeval.runner import aggregate_judge, run_judge_eval


class FakeCorpus:
    def section_text(self, ticket_id, section_name):
        return f"{ticket_id}:{section_name}"

    def narratives(self, ticket_ids):
        return {t: f"narrative-{t}" for t in ticket_ids}


def _queries():
    return [
        Query("q1", "t1", "simple", ["AIT/x"], ["AIT"], [], None, source_tickets=["INC-AIT-0001"]),
        Query("q2", "t2", "simple", ["ALP/y"], ["ALP"], [], None, source_tickets=["INC-ALP-0001"]),
    ]


def _retrieve(arm, q):
    return [RetrievedPoint("INC-AIT-0001", "description", 0.9)]


def _judge():
    return MockJudge({
        (qid, m): 0.8
        for qid in ("q1", "q2")
        for m in (CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY)
    })


def test_run_judge_eval_shape_and_aggregate():
    arms = ["dense", "bm25", "hybrid"]
    res = run_judge_eval(arms, _queries(), _retrieve, FakeCorpus(), _judge(), n_runs=3)
    assert len(res) == 3 * 2 * 2 * 3  # arms × queries × metrics × runs

    agg = aggregate_judge(res)
    mean, sd = agg[("dense", CONTEXTUAL_PRECISION)]
    assert mean == pytest.approx(0.8) and sd == pytest.approx(0.0)  # constant → zero variance


def test_cache_prevents_recalls_across_runs(tmp_path):
    judge = _judge()
    cache = JudgeCache(tmp_path / "judge_cache.json")
    res = run_judge_eval(["dense"], _queries()[:1], _retrieve, FakeCorpus(), judge,
                         n_runs=3, cache=cache)
    assert len(res) == 1 * 1 * 2 * 3  # still 6 recorded results
    assert judge.calls == 2          # but only 2 paid calls (1 per metric); runs 2-3 cached
