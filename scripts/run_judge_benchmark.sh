#!/usr/bin/env sh
# run_judge_benchmark.sh
#
# Whole eval-set, judge-based retrieval benchmark (LLM judge). Prints Table 2 from
# docs/retrieval-evaluation.md: ContextualPrecision + ContextualRelevancy across
# dense / bm25 / hybrid, each query at n runs, bootstrap CI over queries.
# Needs OPENAI_API_KEY. Judge calls are costly, so it scores 15 simple queries by default.
#
# Pair: run_retrieval_benchmark.sh is the label half (no key).
# Per-query diagnostics: run_deepeval_evaluation.sh.
# ─────────────────────────────────────────────────────────────────────────────

set -e

case "${1:-}" in
  -h|--help)
    cat <<'EOF'
run_judge_benchmark.sh — Whole eval-set judge benchmark (LLM judge).

USAGE
    uv run sh scripts/run_judge_benchmark.sh [--k K] [--limit N] [--seed N]

WHAT IT DOES
    Scores simple eval-set queries across dense / bm25 / hybrid with the configured judge:
      - Table 2: ContextualPrecision + ContextualRelevancy, with 95% bootstrap CIs
    Each query is judged at n runs (JUDGE_N_RUNS, default 3). Needs OPENAI_API_KEY.

    Pair:    run_retrieval_benchmark.sh   (label tables, no key)
    Per query: run_deepeval_evaluation.sh

OPTIONS
    --k K        retrieved context depth (default 10)
    --limit N    simple queries to score, in file order (default 15; 0 = all). Costly.
    --seed N     bootstrap resample seed (default 0)
    -h, --help   show this message

PREREQUISITES
    uv sync --group retrieval --group eval
    uv run sh scripts/build_retrieval_index.sh
    OPENAI_API_KEY set in .env
EOF
    exit 0
    ;;
esac

# Quiet the model-load noise
export HF_HUB_VERBOSITY=error
export TRANSFORMERS_VERBOSITY=error
export TQDM_DISABLE=1

PYTHONPATH=src uv run --group retrieval --group eval python3 -m evaluation.deepeval.benchmark "$@"
