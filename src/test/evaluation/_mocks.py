"""
Test-only scaffolding — mock retrievers, a mock judge, and a stub corpus.
"""

from __future__ import annotations

import random
from collections.abc import Mapping

from evaluation.common.contracts import JudgeInput, RetrievedPoint
from evaluation.common.queries import Query
from evaluation.common.relevance import STRICT, RelevanceOracle
from evaluation.common.retriever import RetrievedTicket, Retriever
from evaluation.deepeval.base import JudgeScore
from evaluation.deepeval.runner import RetrieveFn


def _descending_scores(n: int, start: float = 1.0, step: float = 0.01) -> list[float]:
    return [max(start - i * step, 0.0) for i in range(n)]


# ── mock retrievers ───────────────────────────────────────────────────────────────
class PerfectRetriever:
    """Returns all relevant tickets first, then fillers. Every metric should be 1.0."""

    name = "perfect"

    def __init__(self, oracle: RelevanceOracle, level: str = STRICT) -> None:
        self._oracle = oracle
        self._level = level
        self._fillers = sorted(oracle.all_ticket_ids)

    def rank(self, query: Query, k: int) -> list[RetrievedTicket]:
        relevant = set(self._oracle.relevant_tickets(query, self._level))
        gold = [t for t in query.expected_ticket_set if t in relevant]
        rest = sorted(relevant - set(gold))
        ordered = gold + rest + [t for t in self._fillers if t not in relevant]
        ordered = ordered[: max(k, len(relevant))]
        return [RetrievedTicket(t, s) for t, s in zip(ordered, _descending_scores(len(ordered)))]


class WorstRetriever:
    """Returns only NON-relevant tickets. Every relevance-based metric should be 0.0."""

    name = "worst"

    def __init__(self, oracle: RelevanceOracle, level: str = STRICT) -> None:
        self._oracle = oracle
        self._level = level
        self._all = sorted(oracle.all_ticket_ids)

    def rank(self, query: Query, k: int) -> list[RetrievedTicket]:
        relevant = self._oracle.relevant_tickets(query, self._level)
        non_relevant = [t for t in self._all if t not in relevant]
        ordered = non_relevant[:k]
        return [RetrievedTicket(t, s) for t, s in zip(ordered, _descending_scores(len(ordered)))]


class FixtureRetriever:
    """Returns exactly the hand-specified ranking per query_id (golden end-to-end)."""

    def __init__(self, rankings: dict[str, list[str]], name: str = "fixture") -> None:
        self.name = name
        self._rankings = rankings

    def rank(self, query: Query, k: int) -> list[RetrievedTicket]:
        ids = self._rankings.get(query.query_id, [])[:k]
        return [RetrievedTicket(t, s) for t, s in zip(ids, _descending_scores(len(ids)))]


class QualityRetriever:
    """Deterministic, tunable quality: places exactly `hits_in_top_k` relevant tickets at
    the top, then fills with non-relevant. Lets a test assert that better arms score
    higher without randomness."""

    def __init__(
        self,
        oracle: RelevanceOracle,
        hits_in_top_k: int,
        name: str,
        level: str = STRICT,
        seed: int = 0,
    ) -> None:
        self.name = name
        self._oracle = oracle
        self._hits = hits_in_top_k
        self._level = level
        self._all = sorted(oracle.all_ticket_ids)
        self._rng = random.Random(seed)

    def rank(self, query: Query, k: int) -> list[RetrievedTicket]:
        relevant = sorted(self._oracle.relevant_tickets(query, self._level))
        non_relevant = [t for t in self._all if t not in set(relevant)]
        take = min(self._hits, len(relevant), k)
        head = relevant[:take]
        tail = non_relevant[: max(k - take, 0)]
        ordered = head + tail
        return [RetrievedTicket(t, s) for t, s in zip(ordered, _descending_scores(len(ordered)))]


# ── mock judge ────────────────────────────────────────────────────────────────────
class MockJudge:
    """Returns pre-seeded scores keyed by (query_id, metric). For plumbing tests only.
    Counts calls so a cache test can assert the judge was not re-invoked."""

    name = "mock"

    def __init__(self, scores: dict[tuple[str, str], float], default: float = 0.0) -> None:
        self._scores = scores
        self._default = default
        self.calls = 0

    def score(self, case: JudgeInput, metric: str) -> JudgeScore:
        self.calls += 1
        return JudgeScore(metric, self._scores.get((case.query_id, metric), self._default))


# ── stub corpus + mock-arm helpers (offline driver wiring) ─────────────────────────
class DemoCorpus:
    """Offline corpus stub (MockJudge ignores content). The real run uses
    evaluation.adapter.corpus.CorpusReader."""

    def section_text(self, ticket_id: str, section_name: str) -> str:
        return f"[{section_name} of {ticket_id}]"

    def narratives(self, ticket_ids):
        return {t: f"root-cause narrative for {t}" for t in ticket_ids}


def build_mock_arms(oracle: RelevanceOracle) -> Mapping[str, Retriever]:
    """Quality arms with increasing hits (dense < bm25 < hybrid) so assembled
    tables are non-degenerate."""
    return {
        "dense": QualityRetriever(oracle, hits_in_top_k=3, name="dense"),
        "bm25": QualityRetriever(oracle, hits_in_top_k=4, name="bm25"),
        "hybrid": QualityRetriever(oracle, hits_in_top_k=6, name="hybrid"),
    }


def ticket_arms_to_points(arms: Mapping[str, Retriever], k: int = 10) -> RetrieveFn:
    """Bridge ticket-level arms to the point-level judge path (one point per ticket,
    section 'description')."""

    def retrieve(arm_name: str, query: Query) -> list[RetrievedPoint]:
        ranked = arms[arm_name].rank(query, k)
        return [RetrievedPoint(t.ticket_id, "description", t.score) for t in ranked]

    return retrieve
