#!/usr/bin/env sh
# run_classic_evaluation.sh
#
# Classic (label-based, NO LLM) retrieval scoring for one query: precision@k / recall@k /
# nDCG@k at strict and family. Pure id-set membership against the frozen catalog — no key,
# no cost.
#
# Manual ranking (works today — no retriever needed):
#   uv run sh scripts/run_classic_evaluation.sh --query q-ait-diag-1 \
#       --tickets INC-AIT-0032,INC-AIT-0012,INC-AIT-0007
#
# Without --tickets it would run the live retriever's dense/bm25/hybrid arms — NOT built
# yet (src/retrieval/ pending), so that path fails fast with a clear message for now.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# Run as a MODULE (not `python3 src/evaluation/score.py`): the eval package contains a
# subpackage named `deepeval`, and running the file as a script would put src/evaluation/
# on sys.path and shadow the installed `deepeval` library. -m + PYTHONPATH=src avoids that.
PYTHONPATH=src uv run python3 -m evaluation.score --mode classic "$@"
