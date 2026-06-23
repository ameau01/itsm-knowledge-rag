#!/usr/bin/env sh
# run_curation_eval.sh — curation (L2) eval: faithfulness / relevancy / summarization /
# variation, scored by an OpenAI judge across arms (gold + any strategy candidate sets).
#
#   uv run sh scripts/run_curation_eval.sh [--family VDA] [--runs N] [--model gpt-...] \
#       [--candidates-dir eval-set/wiki/candidates] [--no-cache]
#
# Needs OPENAI_API_KEY.
# Judge calls are cached under eval/results/ 
set -e
exec uv run --group eval python3 src/evaluation/curation/run.py "$@"
