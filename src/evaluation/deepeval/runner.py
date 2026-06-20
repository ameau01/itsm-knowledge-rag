"""
Four-arm judge loop and aggregation.

For each arm and query: retrieve points, resolve their redacted texts and the reference
narratives from the corpus, build the judge case, and score each metric over N runs
(variance). Scores route through the optional `JudgeCache` so re-runs and the repeated
variance runs do not re-pay. Aggregation is mean + stdev per (arm, metric), reported
alongside the deterministic table.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ..common.contracts import RetrievedPoint, build_l1_eval_case
from ..common.queries import Query
from .base import JUDGE_METRICS, Judge
from .cache import JudgeCache
from .expected_output import build_expected_output

# A retrieval function: (arm_name, query) -> ranked points. The real Qdrant retriever and
# the mock fixtures both satisfy this; the runner stays agnostic to the IR stack.
RetrieveFn = Callable[[str, Query], list[RetrievedPoint]]


@dataclass(frozen=True)
class JudgeResult:
    arm: str
    query_id: str
    metric: str
    run: int
    score: float


def run_judge_eval(
    arm_names: Sequence[str],
    queries: Sequence[Query],
    retrieve: RetrieveFn,
    corpus,                      # CorpusReader-like: .section_text(tid, section), .narratives(ids)
    judge: Judge,
    *,
    metrics: Sequence[str] = JUDGE_METRICS,
    n_runs: int = 3,
    cache: JudgeCache | None = None,
) -> list[JudgeResult]:
    results: list[JudgeResult] = []
    for arm in arm_names:
        for q in queries:
            points = retrieve(arm, q)
            texts = [corpus.section_text(p.ticket_id, p.section_name) for p in points]
            reference = build_expected_output(q, corpus.narratives(q.source_tickets))
            case = build_l1_eval_case(q, points, texts, reference).to_judge_input()
            for run in range(n_runs):
                for metric in metrics:
                    value: float | None = None
                    ckey = cache.key(judge.name, metric, case) if cache is not None else None
                    if cache is not None and ckey is not None:
                        value = cache.get(ckey)
                    if value is None:
                        value = judge.score(case, metric).value
                        if cache is not None and ckey is not None:
                            cache.put(ckey, value)
                    results.append(JudgeResult(arm, q.query_id, metric, run, value))
    return results


def aggregate_judge(results: Sequence[JudgeResult]) -> dict[tuple[str, str], tuple[float, float]]:
    """(arm, metric) -> (mean, stdev) across all queries and runs."""
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in results:
        buckets[(r.arm, r.metric)].append(r.score)
    return {
        key: (statistics.fmean(vals), statistics.pstdev(vals) if len(vals) > 1 else 0.0)
        for key, vals in buckets.items()
    }
