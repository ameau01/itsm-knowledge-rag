"""
Rank-based retrieval metrics (pure functions).

"""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def _hits_in_top_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> int:
    rel = set(relevant)
    return sum(1 for t in ranked[:k] if t in rel)


def recall_at_k(
    ranked: Sequence[str],
    relevant: Iterable[str],
    k: int,
    n_relevant: int | None = None,
) -> float:
    """Capped recall: hits / min(k, n_relevant). 0.0 when nothing is relevant."""
    rel = set(relevant)
    denom_total = n_relevant if n_relevant is not None else len(rel)
    if denom_total == 0:
        return 0.0
    denom = min(k, denom_total)
    return _hits_in_top_k(ranked, rel, k) / denom


def precision_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Precision@k: relevant tickets in the top-k / number of results in the top-k.
    """
    denom = min(k, len(ranked))
    if denom == 0:
        return 0.0
    return _hits_in_top_k(ranked, relevant, k) / denom


def reciprocal_rank(ranked: Sequence[str], relevant: Iterable[str]) -> float:
    """1 / rank of the first relevant result (1-based); 0.0 if none retrieved."""
    rel = set(relevant)
    for i, ticket in enumerate(ranked):
        if ticket in rel:
            return 1.0 / (i + 1)
    return 0.0
