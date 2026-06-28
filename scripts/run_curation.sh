#!/usr/bin/env sh
# run_curation.sh — multi-agent (orchestrator + aggregator) curation. Reads group tickets and
# writes the five-field curated_description back into wiki_pages, IN PLACE. --db defaults to the
# operational store (override with --db for a separate copy). Tickets must already be ingested.
# Build-time / regeneration tool (needs ANTHROPIC_API_KEY; the demo serves curation from seeds).
#
# Clear curation first to regenerate cleanly:  uv run sh scripts/reset_l2.sh --curation
#
#   uv run sh scripts/run_curation.sh --heaviest --dry-run   # plan only, no API
#   uv run sh scripts/run_curation.sh --family VDA --mock     # Phase-1 gate, no API
#   uv run sh scripts/run_curation.sh --family VDA            # one family (real LLM)
#   uv run sh scripts/run_curation.sh --family ALL            # whole corpus (paid)
#
# Model defaults to settings.multi_agent_model (MULTI_AGENT_MODEL, claude-opus-4-6).
# Score the result with: uv run sh scripts/run_curation_eval.sh --family VDA
set -e
exec uv run --group curation_agent python3 src/curation_agent/run.py "$@"
