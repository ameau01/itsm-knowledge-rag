"""Bootstrap CI: seeded determinism and basic invariants."""

from __future__ import annotations

import pytest

from evaluation.common.bootstrap import bootstrap_ci

VALUES = [0.2, 0.4, 0.6, 0.8, 1.0]


def test_seeded_determinism():
    a = bootstrap_ci(VALUES, seed=42)
    b = bootstrap_ci(VALUES, seed=42)
    assert a == b  # same seed → identical interval


def test_different_seed_can_differ_but_point_is_stable():
    a = bootstrap_ci(VALUES, seed=1)
    b = bootstrap_ci(VALUES, seed=2)
    assert a.point == b.point == pytest.approx(0.6)  # the mean never depends on seed


def test_point_is_the_mean_and_ci_brackets_it():
    ci = bootstrap_ci(VALUES, seed=0)
    assert ci.point == pytest.approx(sum(VALUES) / len(VALUES))
    assert ci.lo <= ci.point <= ci.hi
    assert ci.n == 5


def test_degenerate_all_equal():
    ci = bootstrap_ci([1.0, 1.0, 1.0], seed=0)
    assert ci.point == ci.lo == ci.hi == pytest.approx(1.0)


def test_empty_is_safe():
    ci = bootstrap_ci([], seed=0)
    assert ci.n == 0 and ci.point == 0.0
