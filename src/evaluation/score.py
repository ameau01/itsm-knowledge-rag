"""
Evaluation driver — score retrieval results for one query in two modes:

  classic   label-based, NO LLM. precision@k / recall@k at strict + family.
  deepeval  LLM judge. ContextualPrecision + ContextualRelevancy on the retrieved context.


Sample usage:
    uv run sh scripts/run_classic_evaluation.sh  --query q-ait-diag-1 --arm hybrid
    uv run sh scripts/run_classic_evaluation.sh  --query q-ait-diag-1 --tickets INC-AIT-0032
    uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 --tickets INC-AIT-0032

"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/ on path

from config import PROJECT_ROOT, settings                          # noqa: E402
from evaluation.common.contracts import RetrievedPoint, build_l1_eval_case  # noqa: E402
from evaluation.common.queries import Query, load_queries          # noqa: E402
from evaluation.common.relevance import LENIENT, STRICT, RelevanceOracle  # noqa: E402
from evaluation.deepeval.base import (                             # noqa: E402
    CONTEXTUAL_PRECISION,
    CONTEXTUAL_RELEVANCY,
    Judge,
)
from evaluation.deepeval.expected_output import build_expected_output  # noqa: E402
from evaluation.label_based import metrics_rank as mr               # noqa: E402

DEFAULT_K = 10


# ── scoring cores (pure; reused by the tests with mock inputs) ─────────────────────
def classic_scores(
    query: Query, ranked_ids: list[str], oracle: RelevanceOracle, k: int = DEFAULT_K
) -> dict[str, dict[str, float]]:
    """precision@k / recall@k at strict and family, for one query's ranking."""
    out: dict[str, dict[str, float]] = {}
    for level, name in ((STRICT, "strict"), (LENIENT, "family")):
        relevant = oracle.relevant_tickets(query, level)
        n_rel = len(relevant)
        out[name] = {
            "precision": mr.precision_at_k(ranked_ids, relevant, k),
            "recall": mr.recall_at_k(ranked_ids, relevant, k, n_relevant=n_rel),
            "n_relevant": float(n_rel),
        }
    return out


def deepeval_scores(
    query: Query,
    points: list[RetrievedPoint],
    texts: list[str],
    narratives: dict[str, str],
    judge: Judge,
    n_runs: int,
) -> dict[str, float]:
    """ContextualPrecision + ContextualRelevancy on the retrieved context, averaged over
    n_runs (the committed n=3 protocol)."""
    reference = build_expected_output(query, narratives)
    case = build_l1_eval_case(query, points, texts, reference).to_judge_input()

    def avg(metric: str) -> float:
        return sum(judge.score(case, metric).value for _ in range(n_runs)) / n_runs

    return {
        "contextual_precision": avg(CONTEXTUAL_PRECISION),
        "contextual_relevancy": avg(CONTEXTUAL_RELEVANCY),
    }


# ── CLI helpers ───────────────────────────────────────────────────────────────────
def _load_all_queries() -> dict[str, Query]:
    r = PROJECT_ROOT / "eval-set" / "retrieval"
    qs: list[Query] = []
    for f in ("simple-queries.json", "complex-queries.json", "abstention-queries.json"):
        qs += load_queries(r / f)
    return {q.query_id: q for q in qs}


def _parse_tickets(s: str) -> list[str]:
    return [t.strip() for t in s.split(",") if t.strip()]


def _build_real_judge() -> Judge:
    if not settings.openai_api_key:
        raise SystemExit(
            "DeepEval evaluation FAILED: OPENAI_API_KEY is not set.\n"
            f"  JUDGE_PROVIDER={settings.judge_provider}  JUDGE_MODEL={settings.judge_model}\n"
            "  Add OPENAI_API_KEY to .env. (Classic mode needs no key.)"
        )
    try:
        from evaluation.deepeval.deepeval_judge import DeepEvalJudge
        return DeepEvalJudge(settings.judge_model, api_key=settings.openai_api_key)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            f"DeepEval evaluation FAILED setting up the judge ({settings.judge_model}): "
            f"{type(e).__name__}: {e}\n"
            "  Install the eval deps (uv sync --group eval) and check JUDGE_PROVIDER/JUDGE_MODEL."
        )


def _print_classic(query: Query, ranked: list[str], oracle: RelevanceOracle, k: int) -> None:
    scores = classic_scores(query, ranked, oracle, k)
    print(f"Classic evaluation — query {query.query_id} (manual ranking, k={k})")
    print(f"  ranked: {', '.join(ranked)}")
    for level in ("strict", "family"):
        s = scores[level]
        print(f"  {level:7}: precision@{k}={s['precision']:.3f}  recall@{k}={s['recall']:.3f}  "
              f"(n_relevant={int(s['n_relevant'])})")


def _print_deepeval(query: Query, ranked: list[str], section: str, k: int) -> None:
    from evaluation.adapter.corpus import CorpusReader
    corpus = CorpusReader()
    points = [RetrievedPoint(tid, section, 1.0) for tid in ranked]
    texts = [corpus.section_text(tid, section) for tid in ranked]
    judge = _build_real_judge()
    n = settings.judge_n_runs
    print(f"DeepEval evaluation — query {query.query_id}, judge {settings.judge_model} "
          f"(manual: {len(ranked)} ticket(s), section={section}, n={n})")
    try:
        scores = deepeval_scores(query, points, texts, corpus.narratives(query.source_tickets),
                                 judge, n)
    except Exception as e:  # noqa: BLE001
        corpus.close()
        raise SystemExit(
            f"DeepEval evaluation FAILED calling the judge ({settings.judge_model}): "
            f"{type(e).__name__}: {e}\n  Check OPENAI_API_KEY, network, and JUDGE_MODEL.")
    corpus.close()
    print(f"  ContextualPrecision : {scores['contextual_precision']:.3f}")
    print(f"  ContextualRelevancy : {scores['contextual_relevancy']:.3f}")


def _run_live(query: Query, arm_name: str, mode: str, k: int) -> None:
    """Score one query against the live retriever arm."""
    from evaluation.adapter.corpus import CorpusReader
    try:
        from retrieval import build_arms
        corpus = CorpusReader()
        arms = build_arms()
    except Exception as e:  # noqa: BLE001 — surface deps/Qdrant issues as a clean message
        raise SystemExit(
            f"Live retrieval unavailable ({type(e).__name__}: {e}).\n"
            "  Install deps (uv sync --group retrieval), start Qdrant (docker compose up -d "
            "qdrant), build the index (scripts/build_retrieval_index.sh),\n"
            "  or pass --tickets <id,...> to score a manual ranking.")
    arm = arms.get(arm_name)
    if arm is None:
        raise SystemExit(f"arm {arm_name!r} unavailable.")

    if mode == "classic":
        oracle = RelevanceOracle.from_catalog(PROJECT_ROOT / "eval-set" / "catalog.json")
        ranked = [t.ticket_id for t in arm.rank(query, k)]
        print(f"Classic evaluation — query {query.query_id}, arm {arm_name} (k={k})")
        print(f"  ranked: {', '.join(ranked)}")
        scores = classic_scores(query, ranked, oracle, k)
        for level in ("strict", "family"):
            s = scores[level]
            print(f"  {level:7}: precision@{k}={s['precision']:.3f}  recall@{k}={s['recall']:.3f}  "
                  f"(n_relevant={int(s['n_relevant'])})")
    else:
        points = arm.retrieve_points(query, k)
        texts = [corpus.section_text(p.ticket_id, p.section_name) for p in points]
        judge = _build_real_judge()
        n = settings.judge_n_runs
        print(f"DeepEval evaluation — query {query.query_id}, arm {arm_name}, "
              f"judge {settings.judge_model} (n={n})")
        ev = deepeval_scores(query, points, texts, corpus.narratives(query.source_tickets),
                             judge, n)
        print(f"  ContextualPrecision : {ev['contextual_precision']:.3f}")
        print(f"  ContextualRelevancy : {ev['contextual_relevancy']:.3f}")
    corpus.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Score one query, classic (no LLM) or deepeval.")
    ap.add_argument("--mode", choices=["classic", "deepeval"], required=True)
    ap.add_argument("--query", default=None, help="query_id from the frozen eval-set")
    ap.add_argument("--tickets", default=None,
                    help="comma-separated ticket ids = a MANUAL ranking (no retriever needed)")
    ap.add_argument("--arm", choices=["dense", "bm25", "hybrid"],
                    default="hybrid", help="live retriever arm to use when --tickets is omitted")
    ap.add_argument("--section", default="description",
                    help="deepeval (manual): which ticket section to score (default: description)")
    ap.add_argument("--k", type=int, default=DEFAULT_K)
    args = ap.parse_args()

    if not args.query:
        raise SystemExit("Provide --query <id> (add --tickets <id,...> for a manual ranking).")
    queries = _load_all_queries()
    if args.query not in queries:
        raise SystemExit(f"query {args.query!r} not found in the frozen eval-set.")
    query = queries[args.query]

    if not args.tickets:                       # live retriever path
        _run_live(query, args.arm, args.mode, args.k)
        return

    ranked = _parse_tickets(args.tickets)       # manual ranking path
    if args.mode == "classic":
        oracle = RelevanceOracle.from_catalog(PROJECT_ROOT / "eval-set" / "catalog.json")
        _print_classic(query, ranked, oracle, args.k)
    else:
        _print_deepeval(query, ranked, args.section, args.k)


if __name__ == "__main__":
    main()
