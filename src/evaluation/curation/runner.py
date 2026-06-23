"""Run the curation eval: arms x pages x metrics x runs -> aggregated (mean, stdev).
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import Candidate, CurationJudge, PageMeta, build_curation_cases


@dataclass(frozen=True)
class CurationResult:
    arm: str
    root_cause_id: str
    metric: str
    run: int
    score: float


def run_curation_eval(
    candidates_by_arm: Mapping[str, Sequence[Candidate]],
    page_meta_by_rc: Mapping[str, PageMeta],
    judge: CurationJudge,
    *,
    n_runs: int = 3,
) -> list[CurationResult]:
    results: list[CurationResult] = []
    for arm, candidates in candidates_by_arm.items():
        for cand in candidates:
            meta = page_meta_by_rc[cand.root_cause_id]
            cases = build_curation_cases(
                cand, meta.evidence_pool, multi_ticket=meta.multi_ticket
            )
            for case in cases:
                for run in range(n_runs):
                    score = judge.score(case).value
                    results.append(
                        CurationResult(arm, cand.root_cause_id, case.metric, run, score)
                    )
    return results


def aggregate_curation(
    results: Sequence[CurationResult],
) -> dict[tuple[str, str], tuple[float, float]]:
    """(arm, metric) -> (mean, stdev) across all pages and runs."""
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in results:
        buckets[(r.arm, r.metric)].append(r.score)
    return {
        key: (statistics.fmean(vals), statistics.pstdev(vals) if len(vals) > 1 else 0.0)
        for key, vals in buckets.items()
    }
