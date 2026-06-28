#!/usr/bin/env sh
# reset_l2.sh — clear LLM-authored L2 columns in the operational store so the producers can
# regenerate them in place. Tickets + deterministic wiki_pages columns are left intact.
#
#   uv run sh scripts/reset_l2.sh --curation     # NULL curated_description + curation_details
#   uv run sh scripts/reset_l2.sh --overview     # NULL ai_overview + ai_overview_details
#   uv run sh scripts/reset_l2.sh --all          # both
#   uv run sh scripts/reset_l2.sh --curation --db path/to/other.db
set -e
exec uv run --no-sync python3 src/ingest/reset_l2.py "$@"
