#!/usr/bin/env sh
# run_demo.sh — one command: build the operational store (tickets + curation + AI overview) and
# the embedding index if missing, then start the search app. Idempotent — the build steps run only
# when their output is absent, except the L2 seed load which is always applied.
#
# For manual control, run these separately instead:
#   scripts/run_ingest.sh                # redact corpus -> SQLite (tickets; curation left NULL)
#   scripts/load_seeds.sh --l2-only      # load curation + AI overview from db_seeds/
#   scripts/build_retrieval_index.sh     # embed -> Qdrant
#   scripts/run_streamlit.sh             # serve
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
  echo "[1/4] operational store present — skipping ingest"
else
  echo "[1/4] building operational store (redact)…"
  uv run --no-sync sh scripts/run_ingest.sh
fi

# 2. Apply Curation + AI overview.
echo "[2/4] loading curation + AI overview from db_seeds…"
uv run --no-sync sh scripts/load_seeds.sh --l2-only

# 3. Embedding index (embedded Qdrant on disk).
if [ -d "$VDB" ] && [ -n "$(ls -A "$VDB" 2>/dev/null)" ]; then
  echo "[3/4] vector index present — skipping build (delete $VDB to rebuild)"
else
  echo "[3/4] building embedding index (downloads the model once, ~2 GB)…"
  uv run --no-sync sh scripts/build_retrieval_index.sh
fi

# 4. Serve.
echo "[4/4] starting the search app…"
exec uv run --no-sync sh scripts/run_streamlit.sh "$@"
