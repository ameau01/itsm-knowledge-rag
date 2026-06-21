"""
End-to-end harness validation with mock retrievers.

Proves the *method* works before any real IR exists, under the global (no-intent)
design from docs/retrieval-evaluation.md:
  - a perfect retriever scores 1.0 on the relevance-based metrics,
  - a worst retriever scores 0.0,
  - the report orders arms by quality and excludes Hit Rate.
"""

from __future__ import annotations

from evaluation.label_based.harness import aggregate, run_complex, run_simple
from evaluation.common.relevance import LENIENT, STRICT
from evaluation.label_based.report import TABLE1_COLUMNS, build_arm_table
from _mocks import PerfectRetriever, QualityRetriever, WorstRetriever


def test_perfect_retriever_scores_one(simple_queries, oracle):
    perfect = PerfectRetriever(oracle)
    records = run_simple([perfect], simple_queries, oracle, ks=(5, 10), levels=(STRICT,))
    agg = aggregate(records)
    for (arm, metric, k, level), ci in agg.items():
        if metric in ("recall",):
            assert ci.point == 1.0, f"{metric}@{k} should be 1.0 for a perfect retriever"


def test_worst_retriever_scores_zero(simple_queries, oracle):
    worst = WorstRetriever(oracle)
    records = run_simple([worst], simple_queries, oracle, ks=(5, 10), levels=(STRICT,))
    agg = aggregate(records)
    for (arm, metric, k, level), ci in agg.items():
        if metric in ("recall", "rr"):
            assert ci.point == 0.0, f"{metric}@{k} should be 0.0 for a worst retriever"


def test_every_query_gets_the_same_global_metrics(simple_queries, oracle):
    """No intent routing: each query yields the same metric set."""
    perfect = PerfectRetriever(oracle)
    records = run_simple([perfect], simple_queries, oracle, ks=(10,), levels=(STRICT, LENIENT))
    by_query: dict[str, set[str]] = {}
    for r in records:
        by_query.setdefault(r.query_id, set()).add(r.metric)
    metric_sets = {frozenset(m) for m in by_query.values()}
    assert metric_sets == {frozenset({"recall", "rr"})}


def test_report_orders_arms_and_excludes_hit_rate(simple_queries, oracle):
    arms = [
        QualityRetriever(oracle, hits_in_top_k=2, name="dense"),
        QualityRetriever(oracle, hits_in_top_k=5, name="hybrid"),
        QualityRetriever(oracle, hits_in_top_k=10, name="bm25"),
    ]
    records = run_simple(arms, simple_queries, oracle, ks=(10,), levels=(STRICT, LENIENT))
    agg = aggregate(records)
    table = build_arm_table(agg, ["dense", "hybrid", "bm25"], k=10)

    assert [r.arm for r in table.rows] == ["bm25", "hybrid", "dense"]
    primary = TABLE1_COLUMNS[0].label
    points = [r.cells[primary].point for r in table.rows]
    assert points[0] > points[1] > points[2]  # monotonic quality
    assert table.columns == ("Recall@10 (strict)", "Recall@10 (family)")
    assert not any("hit" in c.lower() for c in table.columns)


def test_complex_candidate_set_runs(complex_queries, oracle):
    perfect = PerfectRetriever(oracle)
    scores = run_complex(perfect, complex_queries, oracle, k=10)
    assert len(scores) == len(complex_queries)
    # a perfect retriever surfaces the expected causes → recall should be high
    assert all(s.recall > 0 for s in scores.values())
