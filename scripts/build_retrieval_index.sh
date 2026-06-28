#!/usr/bin/env sh
# build_retrieval_index.sh
#
# Embed the operational store's ticket sections and upsert them into Qdrant.
# Idempotent — safe to re-run (points overwrite in place).
#
# Prerequisites:
#   uv sync --group retrieval          # embedding + qdrant deps
#   (operational store already built by scripts/run_ingest.sh)
#   Qdrant runs embedded on disk by default (QDRANT_LOCAL=true) — nothing to start. For a
#   server, set QDRANT_LOCAL=false and run `docker compose up -d qdrant` first.
#
# Usage:
#   uv run sh scripts/build_retrieval_index.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

# --no-sync (not --group): the env is already synced (locally via `uv sync --group retrieval`,
PYTHONPATH=src uv run --no-sync python3 -m retrieval.ingest "$@"
