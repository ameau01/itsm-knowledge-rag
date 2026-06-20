"""
Fixtures for the evaluation-harness tests.

Adds `src/` to sys.path (matching the repo's flat-layout test convention) and loads the
real frozen eval-set files so the oracle and query loaders are exercised against actual
data, not toy stand-ins.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2]  # src/test/eval -> src
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# This directory on sys.path so the evaluation tests can `import _mocks` (test-only
# scaffolding: mock retrievers, MockJudge, stub corpus — kept out of src/).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

_REPO = _SRC.parent  # repo root
_EVAL_SET = _REPO / "eval-set"
_RETRIEVAL = _EVAL_SET / "retrieval"

from evaluation.common.queries import load_queries  # noqa: E402
from evaluation.common.relevance import RelevanceOracle  # noqa: E402


@pytest.fixture(scope="session")
def catalog_path() -> Path:
    return _EVAL_SET / "catalog.json"


@pytest.fixture(scope="session")
def oracle(catalog_path: Path) -> RelevanceOracle:
    return RelevanceOracle.from_catalog(catalog_path)


@pytest.fixture(scope="session")
def simple_queries():
    return load_queries(_RETRIEVAL / "simple-queries.json")


@pytest.fixture(scope="session")
def complex_queries():
    return load_queries(_RETRIEVAL / "complex-queries.json")


@pytest.fixture(scope="session")
def abstention_queries():
    return load_queries(_RETRIEVAL / "abstention-queries.json")
