#!/usr/bin/env sh
# export_seeds.sh — regenerate the committed SQL seeds (tickets.sql, curated_content.sql, ai_overview.sql) from a curated db. 
#
#   uv run sh scripts/export_seeds.sh --db <curated.db> --out db_seeds
set -e
exec uv run --no-sync python3 src/ingest/export_seeds.py "$@"
