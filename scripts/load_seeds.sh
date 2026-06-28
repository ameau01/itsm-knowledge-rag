#!/usr/bin/env sh
# load_seeds.sh — populate the operational store from committed SQL seeds.
# No HF download, no redaction, no LLM. Separate from run_ingest.sh (the HF/live path).
#
#   uv run sh scripts/load_seeds.sh                # --full: tickets + wiki_pages + L2 (mock / rag-demo)
#   uv run sh scripts/load_seeds.sh --l2-only      # only curation + overview (after run_ingest, live)
#   uv run sh scripts/load_seeds.sh --seeds-dir <dir>
#
# DB location: $OPERATIONAL_STORE/itsm_rag.db (default .operational_store/itsm_rag.db).
set -e
exec uv run --no-sync python3 src/ingest/load_seeds.py "$@"
