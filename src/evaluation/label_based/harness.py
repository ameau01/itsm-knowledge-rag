"""
Evaluation harness — orchestration.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from . import metrics_rank as mr
from .abstention import ScoredQuery, calibrate_floor, evaluate_abstention
from ..common.bootstrap import CI, bootstrap_ci
from .metrics_set import CandidateSetScore, score_candidate_set
from ..common.queries import Query
from ..common.relevance import LENIENT, STRICT, RelevanceOracle
from ..common.retriever import Retriever, ticket_ids

RANKING_METRICS = ("recall", "ndcg")


@dataclass(frozen=True)
class PerQueryResult:
    arm: str
    query_id: str
    metric: str
    k: int
    level: str
    value: float


def run_simple(
    arms: Sequence[Retriever],
    queries: Sequence[Query],
    oracle: RelevanceOracle,
    ks: Sequence[int] = (5, 10),
    levels: Sequence[str] = (STRICT, LENIENT),
) -> list[PerQueryResult]:
    """Per-query recall@k and nDCG@k at each level, plus a strict reciprocal rank.

    No intent routing — the same metrics are computed for every query. This same path
    is reused for the complex set (its strict relevant set is the union of the query's
    expected_root_cause clusters), giving complex recall@k / nDCG@k for free."""
    out: list[PerQueryResult] = []
    max_k = max(ks)
    for arm in arms:
        for q in queries:
            ranked = ticket_ids(arm.rank(q, max_k))
            for level in levels:
                relevant = oracle.relevant_tickets(q, level)
                n_rel = len(relevant)
                for k in ks:
                    out.append(PerQueryResult(arm.name, q.query_id, "recall", k, level,
                                              mr.recall_at_k(ranked, relevant, k, n_relevant=n_rel)))
                    out.append(PerQueryResult(arm.name, q.query_id, "ndcg", k, level,
                                              mr.ndcg_at_k(ranked, relevant, k)))
            # MRR: one reciprocal rank per query, strict relevance, full retrieved depth.
            rr = mr.reciprocal_rank(ranked, oracle.relevant_tickets(q, STRICT))
            out.append(PerQueryResult(arm.name, q.query_id, "rr", max_k, STRICT, rr))
    return out


def aggregate(records: Sequence[PerQueryResult], seed: int = 0) -> dict[tuple, CI]:
    """Group per-query values by (arm, metric, k, level) and bootstrap each group's mean.

    Computed once over the full set — the retriever has no parameters fit on the queries,
    so uncertainty is a bootstrap CI, not cross-validation."""
    groups: dict[tuple, list[float]] = defaultdict(list)
    for r in records:
        groups[(r.arm, r.metric, r.k, r.level)].append(r.value)
    return {key: bootstrap_ci(vals, seed=seed) for key, vals in groups.items()}


# ── complex (candidate-set) ──────────────────────────────────────────────────────
def predicted_root_causes(ranked: list[str], oracle: RelevanceOracle, k: int) -> set[str]:
    """Derive the predicted candidate set: the distinct root causes present in top-k."""
    out: set[str] = set()
    for t in ranked[:k]:
        rc = oracle.root_cause_of(t)
        if rc is not None:
            out.add(rc)
    return out


def run_complex(
    arm: Retriever, queries: Sequence[Query], oracle: RelevanceOracle, k: int = 10
) -> dict[str, CandidateSetScore]:
    """Candidate-set score per complex query for one arm (recall over the expected
    root-cause set, with an over-hedging penalty). Ticket-level recall@k / nDCG@k for
    the complex set come from run_simple, whose strict relevant set already unions the
    query's multiple expected_root_cause clusters."""
    scores: dict[str, CandidateSetScore] = {}
    for q in queries:
        ranked = ticket_ids(arm.rank(q, k))
        pred = predicted_root_causes(ranked, oracle, k)
        scores[q.query_id] = score_candidate_set(pred, q.expected_root_cause, q.anchor_root_cause)
    return scores


# ── abstention (one-class calibration) ────────────────────────────────────────────
def top_scores(arm: Retriever, queries: Sequence[Query], k: int = 10) -> dict[str, float]:
    """Top fused score per query (the abstention signal lives at rank 1)."""
    out: dict[str, float] = {}
    for q in queries:
        ranked = arm.rank(q, k)
        out[q.query_id] = ranked[0].score if ranked else 0.0
    return out


def run_abstention(
    arm: Retriever,
    answerable: Sequence[Query],
    abstention_queries: Sequence[Query],
    percentile: float,
    k: int = 10,
):
    """
    Calibrate the floor on the answerable (in-corpus) top-scores ONLY, then evaluate on
    answerable + abstention together. Returns (floor, AbstentionReport).
    """
    in_corpus = list(top_scores(arm, answerable, k).values())
    floor = calibrate_floor(in_corpus, percentile)

    scored: list[ScoredQuery] = []
    for q in answerable:
        scored.append(ScoredQuery(top_score=top_scores(arm, [q], k)[q.query_id], should_abstain=False))
    for q in abstention_queries:
        scored.append(ScoredQuery(top_score=top_scores(arm, [q], k)[q.query_id], should_abstain=True))
    return floor, evaluate_abstention(scored, floor)
