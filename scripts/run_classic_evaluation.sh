#!/usr/bin/env sh
# run_classic_evaluation.sh
#
# Classic (label-based, NO LLM) retrieval scoring for one query: precision@k / recall@k
# at strict and family. Pure id-set membership against the frozen catalog, no key, no cost.
#
# This script runs classic scoring only. For the LLM judge, use run_deepeval_evaluation.sh.
#
# Score a manually supplied ranking:
#   uv run sh scripts/run_classic_evaluation.sh --query q-ait-diag-1 \
#       --tickets INC-AIT-0032,INC-AIT-0012,INC-AIT-0007
#
# Without --tickets it runs the live dense/bm25/hybrid arms; if live retrieval is not
# configured, that path exits with a clear message.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# This wrapper owns the mode. The underlying scorer is shared and supports both classic and
# deepeval, but each is reachable ONLY through its own script. Mode is never selectable here:
# a stray --mode is rejected, so a classic run can never turn into a judge run.
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat <<'EOF'
run_classic_evaluation.sh — Classic (label-based, no LLM) retrieval scoring.

USAGE
    uv run sh scripts/run_classic_evaluation.sh --query QUERY_ID [OPTIONS]

OPTIONS
    --query QUERY               query_id from the frozen eval-set (required)
    --tickets IDS               comma-separated ticket ids = a MANUAL ranking (no retriever)
    --arm {dense,bm25,hybrid}   live arm to use when --tickets is omitted
    --k K                       cutoff for precision@k / recall@k
    -h, --help                  show this message

    Scores precision@k / recall@k at strict and family levels. No key, no cost.
    For judge-based scoring (ContextualPrecision / Relevancy), use
    scripts/run_deepeval_evaluation.sh.

EXAMPLES
    uv run sh scripts/run_classic_evaluation.sh --query q-ait-diag-1 --arm hybrid
    uv run sh scripts/run_classic_evaluation.sh --query q-ait-diag-1 \
        --tickets INC-AIT-0032,INC-AIT-0012,INC-AIT-0007
EOF
      exit 0
      ;;
    --mode|--mode=*)
      echo "run_classic_evaluation.sh runs classic scoring only; mode is not selectable." >&2
      echo "For the LLM judge, use: uv run sh scripts/run_deepeval_evaluation.sh" >&2
      exit 2
      ;;
  esac
done

# Quiet the model-load noise
export HF_HUB_VERBOSITY=error
export TRANSFORMERS_VERBOSITY=error
export TQDM_DISABLE=1

# Run as a MODULE (not `python3 src/evaluation/score.py`): the eval package contains a
# subpackage named `deepeval`, and running the file as a script would put src/evaluation/
# on sys.path and shadow the installed `deepeval` library. -m + PYTHONPATH=src avoids that.
PYTHONPATH=src uv run --group retrieval python3 -m evaluation.score --mode classic "$@"
