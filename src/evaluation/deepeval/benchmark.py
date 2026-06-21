"""
Whole eval-set judge benchmark — the driver behind Table 2 of docs/retrieval-evaluation.md.

Scores retrieved context with the configured DeepEval judge: ContextualPrecision and
ContextualRelevancy across dense / bm25 / hybrid. Each query is judged at n runs, then the
per-query means are aggregated with a bootstrap CI over queries. Needs OPENAI_API_KEY.

This is the judge half of the benchmark pair. The label half (no key) is
evaluation.label_based.benchmark.

Trigger:  uv run sh scripts/run_judge_benchmark.sh
Direct:   PYTHONPATH=src uv run --group retrieval --group eval \
              python3 -m evaluation.deepeval.benchmark
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on path

from config import PROJECT_ROOT, settings                  # noqa: E402
from evaluation.common.bootstrap import CI, bootstrap_ci    # noqa: E402
from evaluation.common.queries import Query, load_queries   # noqa: E402
from evaluation.score import _build_real_judge, deepeval_scores  # noqa: E402

ARM_ORDER = ("dense", "bm25", "hybrid")
DEFAULT_K = 10
# Judge calls are costly: limit × arms × n runs × 2 metrics. The doc's Table 2 uses 15.
DEFAULT_LIMIT = 15


def _simple_queries(limit: int) -> list[Query]:
    qs = load_queries(PROJECT_ROOT / "eval-set" / "retrieval" / "simple-queries.json")
    return qs if limit <= 0 else qs[:limit]


def _cell(ci: CI) -> str:
    return f"{ci.point:.3f} [{ci.lo:.3f}, {ci.hi:.3f}]"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Whole eval-set judge benchmark (ContextualPrecision / Relevancy).")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help="retrieved context depth")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help="number of simple queries to score, in file order (0 = all). "
                         "Judge calls are costly.")
    ap.add_argument("--seed", type=int, default=0, help="bootstrap resample seed")
    args = ap.parse_args()

    queries = _simple_queries(args.limit)

    try:
        from evaluation.adapter.corpus import CorpusReader
        from retrieval import build_arms
        corpus = CorpusReader()
        arms_map = build_arms()
    except Exception as e:  # noqa: BLE001 — surface deps/Qdrant issues as a clean message
        raise SystemExit(
            f"Live retrieval unavailable ({type(e).__name__}: {e}).\n"
            "  Install deps (uv sync --group retrieval --group eval) and build the index "
            "(uv run sh scripts/build_retrieval_index.sh).")

    judge = _build_real_judge()          # exits cleanly if OPENAI_API_KEY is unset
    n = settings.judge_n_runs
    arms = [(name, arms_map[name]) for name in ARM_ORDER if name in arms_map]

    print(f"Judge: {settings.judge_model}  n={n} runs/query  "
          f"queries={len(queries)} simple (file order)  seed={args.seed}")
    print("\n**Table 2: semantic quality (judge)**\n")
    print("| Arm | Contextual Precision | Contextual Relevancy |")
    print("|---|---|---|")
    try:
        for name, arm in arms:
            cps: list[float] = []
            crs: list[float] = []
            for q in queries:
                points = arm.retrieve_points(q, args.k)
                texts = [corpus.section_text(p.ticket_id, p.section_name) for p in points]
                ev = deepeval_scores(q, points, texts,
                                     corpus.narratives(q.source_tickets), judge, n)
                cps.append(ev["contextual_precision"])
                crs.append(ev["contextual_relevancy"])
            cp = bootstrap_ci(cps, seed=args.seed)
            cr = bootstrap_ci(crs, seed=args.seed)
            print(f"| {name} | {_cell(cp)} | {_cell(cr)} |")
    finally:
        corpus.close()


if __name__ == "__main__":
    main()
