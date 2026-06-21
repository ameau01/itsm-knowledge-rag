#!/usr/bin/env sh
# run_demo.sh — one command: build the operational store + embedding index if they are
# missing, then start the search app. Idempotent. The build steps run only when their output
# is absent, so a second run just launches the app.
#
# For manual control, run these three separately instead:
#   scripts/run_ingest.sh           # redact corpus -> SQLite
#   scripts/build_retrieval_index.sh# embed -> Qdrant
#   scripts/run_streamlit.sh        # serve
#
#   uv run sh scripts/run_demo.sh
#   uv run sh scripts/run_demo.sh --port 8000
#
# Targets the default embedded Qdrant (QDRANT_LOCAL=true). For a Qdrant server, run the steps
# manually so you control when the server is up.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# Load .env so OPERATIONAL_STORE / LOCAL_VECTOR_DB_PATH resolve here.
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi
STORE="${OPERATIONAL_STORE:-.operational_store}"
VDB="${LOCAL_VECTOR_DB_PATH:-.vector_db}"

# 1. Operational store (redacted tickets).
if [ -f "$STORE/itsm_rag.db" ]; then
  echo "[1/3] operational store present — skipping ingest"
else
  echo "[1/3] building operational store (redact)…"
  uv run sh scripts/run_ingest.sh
fi

# 2. Embedding index (embedded Qdrant on disk).
if [ -d "$VDB" ] && [ -n "$(ls -A "$VDB" 2>/dev/null)" ]; then
  echo "[2/3] vector index present — skipping build (delete $VDB to rebuild)"
else
  echo "[2/3] building embedding index (downloads the model once, ~2 GB)…"
  uv run sh scripts/build_retrieval_index.sh
fi

# 3. Serve.
echo "[3/3] starting the search app…"
exec uv run sh scripts/run_streamlit.sh "$@"
