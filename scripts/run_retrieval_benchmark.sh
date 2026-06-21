#!/usr/bin/env sh
# run_retrieval_benchmark.sh
#
# Whole eval-set, label-based retrieval benchmark (NO LLM, no key). Prints the headline
# label tables from docs/retrieval-evaluation.md: retrieval performance with bootstrap CIs,
# MRR, complex candidate-set recall, and abstention, across dense / bm25 / hybrid.
#
# Pair: run_judge_benchmark.sh is the judge half (needs a key).
# Per-query diagnostics: run_classic_evaluation.sh.
# ─────────────────────────────────────────────────────────────────────────────

set -e

case "${1:-}" in
  -h|--help)
    cat <<'EOF'
run_retrieval_benchmark.sh — Whole eval-set label-based benchmark (no LLM).

USAGE
    uv run sh scripts/run_retrieval_benchmark.sh [--k K] [--seed N]

WHAT IT DOES
    Scores the full frozen eval-set across dense / bm25 / hybrid and prints:
      - Table 1: recall@k (strict + family) with 95% bootstrap CIs
      - MRR (strict)
      - Complex: candidate-set recall@k
      - Abstention: accuracy + false-abstention rate per arm
    No key, no cost.

    Pair:    run_judge_benchmark.sh    (judge tables, needs OPENAI_API_KEY)
    Per query: run_classic_evaluation.sh

OPTIONS
    --k K        cutoff for recall@k / MRR depth (default 10)
    --seed N     bootstrap resample seed (default 0)
    -h, --help   show this message

PREREQUISITES
    uv sync --group retrieval
    uv run sh scripts/build_retrieval_index.sh
EOF
    exit 0
    ;;
esac

# Quiet the model-load noise
export HF_HUB_VERBOSITY=error
export TRANSFORMERS_VERBOSITY=error
export TQDM_DISABLE=1

PYTHONPATH=src uv run --group retrieval python3 -m evaluation.label_based.benchmark "$@"
