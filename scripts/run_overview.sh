#!/usr/bin/env sh
# run_overview.sh — generate AI overviews into wiki_pages.ai_overview from curated_description.
# Build-time / regeneration tool (needs ANTHROPIC_API_KEY; the demo serves overviews from seeds).
#
#   uv run sh scripts/run_overview.sh --mock --limit 3    # no API, plumbing check
#   uv run sh scripts/run_overview.sh --family VDA        # one family
#   uv run sh scripts/run_overview.sh --all               # every curated page
#   uv run sh scripts/run_overview.sh --verify            # read back + check (no writes)
set -e
exec uv run --group overview python3 src/overview/run.py "$@"
