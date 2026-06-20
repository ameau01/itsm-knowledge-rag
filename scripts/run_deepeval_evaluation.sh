#!/usr/bin/env sh
# run_deepeval_evaluation.sh
#
# DeepEval (LLM judge) retrieval scoring for one query: ContextualPrecision +
# ContextualRelevancy on the retrieved context, at n=3. Uses the configured judge (real
# LLM) and the operational store; fails fast if OPENAI_API_KEY is unset.
#
# Manual ranking (works today — no retriever needed; resolves the ticket's real section):
#   uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 --tickets INC-AIT-0032
#   uv run sh scripts/run_deepeval_evaluation.sh --query q-ait-diag-1 --tickets INC-AIT-0032 --section resolution
#
# Without --tickets it would run the live retriever's arms — NOT built yet
# (src/retrieval/ pending), so that path fails fast with a clear message for now.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# Run as a MODULE (not `python3 src/evaluation/score.py`): the eval package contains a
# subpackage named `deepeval`, and running the file as a script would put src/evaluation/
# on sys.path and shadow the installed `deepeval` library. -m + PYTHONPATH=src avoids that.
PYTHONPATH=src uv run python3 -m evaluation.score --mode deepeval "$@"
