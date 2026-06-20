"""
Bootstrap confidence intervals.

Per NEXT_PHASE.md: the retriever has no parameters fit on the query set, so ranking
metrics are reported with bootstrap CIs over the full query set — NOT cross-validation.
Each aggregate metric is a mean of per-query values, so we resample the per-query values
with replacement. Seeded for reproducibility (the determinism test pins this).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CI:
    point: float   # the observed statistic on the full sample (mean)
    lo: float      # lower percentile bound
    hi: float      # upper percentile bound
    n: int         # sample size (report this — it is small per intent)


def bootstrap_ci(
    per_query_values: Sequence[float],
    n_resamples: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> CI:
    """
    Percentile bootstrap CI for the mean of per-query metric values.

    Deterministic given `seed`. Wide intervals at small n (e.g. exact_match, n=10) are
    the honest answer, not a bug.
    """
    values = np.asarray(list(per_query_values), dtype=float)
    n = values.size
    if n == 0:
        return CI(point=0.0, lo=0.0, hi=0.0, n=0)

    point = float(values.mean())
    rng = np.random.default_rng(seed)
    # (n_resamples, n) matrix of resampled indices → resampled means
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = values[idx].mean(axis=1)
    lo = float(np.percentile(means, 100 * (alpha / 2)))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return CI(point=point, lo=lo, hi=hi, n=n)
