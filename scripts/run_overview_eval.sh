#!/usr/bin/env sh
# run_overview_eval.sh — overview (L2) eval: overview_quality / faithfulness / summarization,
# plus the deterministic low-hedge guard. Judge is OpenAI (needs OPENAI_API_KEY).
#
#   uv run sh scripts/run_overview_eval.sh --all --runs 3
#   uv run sh scripts/run_overview_eval.sh --all --metric all
#   uv run sh scripts/run_overview_eval.sh --dry-run --limit 3   # no API
set -e
exec uv run --group eval python3 src/evaluation/overview/run.py "$@"
