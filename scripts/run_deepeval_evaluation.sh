#!/usr/bin/env sh
# run_deepeval_evaluation.sh
#
# DeepEval (LLM judge) retrieval scoring for one query: ContextualPrecision +
# ContextualRelevancy on the retrieved context, at n=3. Uses the configured judge (real
# LLM) and the operational store; fails fast if OPENAI_API_KEY is unset.
#
# This script runs deepeval scoring only. For label-based scoring, use run_classic_evaluation.sh.
#
# Score a manually supplied ranking (resolves the ticket's real section text):
#   uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 --tickets INC-AIT-0032
#   uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 --tickets INC-AIT-0032 --section resolution
#
# Without --tickets it runs the live arms; if live retrieval is not configured, that path
# exits with a clear message.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# This wrapper owns the mode. The underlying scorer is shared and supports both classic and
# deepeval, but each is reachable ONLY through its own script. Mode is never selectable here:
# a stray --mode is rejected, so a judge run can never silently fall back to classic.
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat <<'EOF'
run_deepeval_evaluation.sh — DeepEval (LLM judge) retrieval scoring.

USAGE
    uv run sh scripts/run_deepeval_evaluation.sh --query QUERY_ID [OPTIONS]

OPTIONS
    --query QUERY               query_id from the frozen eval-set (required)
    --tickets IDS               comma-separated ticket ids = a MANUAL ranking (no retriever)
    --arm {dense,bm25,hybrid}   live arm to use when --tickets is omitted
    --section SECTION           ticket section to score for a manual ranking (default: description)
    --k K                       cutoff
    -h, --help                  show this message

    Scores ContextualPrecision + ContextualRelevancy with the configured judge (n=3).
    Needs OPENAI_API_KEY. For label-based scoring (no key, no cost), use
    scripts/run_classic_evaluation.sh.

EXAMPLES
    uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 --arm hybrid
    uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 \
        --tickets INC-AIT-0032 --section resolution
EOF
      exit 0
      ;;
    --mode|--mode=*)
      echo "run_deepeval_evaluation.sh runs deepeval scoring only; mode is not selectable." >&2
      echo "For label-based scoring, use: uv run sh scripts/run_classic_evaluation.sh" >&2
      exit 2
      ;;
  esac
done

# Quiet the model-load noise (HF "unauthenticated requests" warning + the "Loading weights"
# tqdm bar from sentence-transformers). Safe here: scoring loads models but never ingests,
# so disabling tqdm hides nothing useful. The ingest script keeps its progress bars.
export HF_HUB_VERBOSITY=error
export TRANSFORMERS_VERBOSITY=error
export TQDM_DISABLE=1

# Run as a MODULE (not `python3 src/evaluation/score.py`): the eval package contains a
# subpackage named `deepeval`, and running the file as a script would put src/evaluation/
# on sys.path and shadow the installed `deepeval` library. -m + PYTHONPATH=src avoids that.
# Needs both groups: retrieval (live arm) + eval (deepeval judge).
PYTHONPATH=src uv run --group retrieval --group eval python3 -m evaluation.score --mode deepeval "$@"
