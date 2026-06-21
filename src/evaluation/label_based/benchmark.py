"""
Whole eval-set label-based benchmark — the driver behind docs/retrieval-evaluation.md.

Loads the frozen eval-set, builds the live arms (dense / bm25 / hybrid), and prints the
headline label-based tables: retrieval performance with bootstrap CIs (Table 1), MRR,
complex candidate-set recall, and abstention per arm. No LLM, no key.

This is the label half of the benchmark pair. The judge half (ContextualPrecision /
Relevancy, needs a key) is evaluation.deepeval.benchmark.

Trigger:  uv run sh scripts/run_retrieval_benchmark.sh
Direct:   PYTHONPATH=src uv run --group retrieval python3 -m evaluation.label_based.benchmark
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

from config import PROJECT_ROOT, settings                       # noqa: E402
from evaluation.common.queries import Query, load_queries        # noqa: E402
from evaluation.common.relevance import STRICT, RelevanceOracle  # noqa: E402
from evaluation.label_based.harness import (                     # noqa: E402
    aggregate,
    run_abstention,
    run_complex,
    run_simple,
)
from evaluation.label_based.report import (                      # noqa: E402
    abstention_to_markdown,
    build_arm_table,
    complex_to_markdown,
    to_markdown,
)

ARM_ORDER = ("dense", "bm25", "hybrid")
DEFAULT_K = 10


def _queries(name: str) -> list[Query]:
    return load_queries(PROJECT_ROOT / "eval-set" / "retrieval" / name)


def _build_arms_or_exit():
    try:
        from retrieval import build_arms
        return build_arms()
    except Exception as e:  # noqa: BLE001 — surface deps/Qdrant issues as a clean message
        raise SystemExit(
            f"Live retrieval unavailable ({type(e).__name__}: {e}).\n"
            "  Install deps (uv sync --group retrieval) and build the index "
            "(uv run sh scripts/build_retrieval_index.sh).")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Whole eval-set label-based retrieval benchmark (no LLM).")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help="cutoff for recall@k / MRR depth")
    ap.add_argument("--seed", type=int, default=0, help="bootstrap resample seed")
    args = ap.parse_args()

    simple = _queries("simple-queries.json")
    complex_q = _queries("complex-queries.json")
    abstain = _queries("abstention-queries.json")
    oracle = RelevanceOracle.from_catalog(PROJECT_ROOT / "eval-set" / "catalog.json")

    arms_map = _build_arms_or_exit()
    arms = [arms_map[n] for n in ARM_ORDER if n in arms_map]
    arm_names = [a.name for a in arms]

    print(f"Eval-set: {len(simple)} simple, {len(complex_q)} complex, "
          f"{len(abstain)} abstention. Arms: {', '.join(arm_names)}. "
          f"Bootstrap seed {args.seed}.\n")

    # ── Table 1: retrieval performance on simple queries (recall@k, bootstrap CI) ──
    records = run_simple(arms, simple, oracle, ks=(args.k,))
    agg = aggregate(records, seed=args.seed)
    table1 = build_arm_table(agg, arm_names, k=args.k,
                             title=f"Table 1: retrieval performance (@{args.k})")
    print(to_markdown(table1))

    # MRR — one figure per arm (strict, full retrieved depth)
    print("\nMRR (strict):")
    for name in arm_names:
        ci = agg.get((name, "rr", args.k, STRICT))
        if ci is not None:
            print(f"  {name}: {ci.point:.3f}")

    # ── Complex: mean candidate-set recall@k per arm ──
    complex_recall = {}
    for a in arms:
        scores = run_complex(a, complex_q, oracle, k=args.k)
        complex_recall[a.name] = (
            sum(s.recall for s in scores.values()) / len(scores) if scores else 0.0)
    print("\n" + complex_to_markdown(complex_recall, arm_names, k=args.k))

    # ── Abstention: per arm. Dense top-1 cosine is the shipped signal ──
    reports = {}
    for a in arms:
        _floor, rep = run_abstention(
            a, list(simple) + list(complex_q), abstain,
            settings.abstention_percentile, k=args.k)
        reports[a.name] = rep
    print("\n" + abstention_to_markdown(reports, arm_names))
    print("\nAbstention signal: dense top-1 cosine (see docs/retrieval-evaluation.md). "
          "The dense arm row is the shipped configuration.")


if __name__ == "__main__":
    main()
