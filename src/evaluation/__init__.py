"""
Retrieval evaluation harness (L1).

Layout:
  common/      shared pure foundation (queries, relevance, bootstrap, retriever, contracts)
  label_based/ deterministic metrics + global harness + Table 1   (no LLM)
  deepeval/    judge-based metrics: DeepEval ContextualPrecision/Relevancy + Table 2
  adapter/     the only IO — corpus reader (SQLite)
"""

from .common.bootstrap import CI, bootstrap_ci
from .common.contracts import (
    NO_GENERATION,
    JudgeInput,
    L1EvalCase,
    RetrievedPoint,
    build_l1_eval_case,
    dedupe_to_tickets,
)
from .common.queries import Query, load_queries
from .common.relevance import LENIENT, STRICT, RelevanceOracle
from .common.retriever import RetrievedTicket, Retriever
from .deepeval.base import JUDGE_METRICS, Judge, JudgeScore
from .deepeval.runner import JudgeResult, aggregate_judge, run_judge_eval
from .label_based.harness import aggregate, run_abstention, run_complex, run_simple
from .label_based.report import build_arm_table

__all__ = [
    "load_queries", "Query", "RelevanceOracle", "STRICT", "LENIENT",
    "bootstrap_ci", "CI", "Retriever", "RetrievedTicket",
    "RetrievedPoint", "L1EvalCase", "JudgeInput", "build_l1_eval_case",
    "dedupe_to_tickets", "NO_GENERATION",
    "run_simple", "aggregate", "run_complex", "run_abstention", "build_arm_table",
    "Judge", "JudgeScore", "JUDGE_METRICS",
    "run_judge_eval", "aggregate_judge", "JudgeResult",
]
