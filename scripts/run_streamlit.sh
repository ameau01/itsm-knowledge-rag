#!/usr/bin/env sh
# run_streamlit.sh — Launch the Streamlit ticket-search app locally.
#
# Usage (always --no-sync: a bare `uv run` re-syncs to the default groups and strips the
# optional `app`/`retrieval` groups this app needs, so launch it with --no-sync):
#   uv run --no-sync sh scripts/run_streamlit.sh                 # serve on :8501
#   uv run --no-sync sh scripts/run_streamlit.sh --port 8000     # custom port
#   uv run --no-sync sh scripts/run_streamlit.sh --help
#   Any extra args after the script are passed straight to `streamlit run`.
#
# Prerequisites:
#   uv sync --group app --group retrieval   # streamlit + live hybrid retrieval (Qdrant + embed)
#   uv run --no-sync sh scripts/run_ingest.sh   # populates the SQLite store the app reads
#
# Environment (read from the shell or a project-root .env, which is sourced here):
#   OPERATIONAL_STORE   SQLite store directory (default: .operational_store)
#   SUPPORT_VIEW_PORT   Default port when --port is not given (default: 8501)
#
# Runs from the repo root so .env and the OPERATIONAL_STORE path resolve correctly.
# ─────────────────────────────────────────────────────────────────────────────

set -e

# ── Help ───────────────────────────────────────────────────────────────────────
case "${1:-}" in
  -h|--help)
    cat <<'EOF'
run_streamlit.sh — Launch the Streamlit ticket-search app locally.

USAGE
    uv run --no-sync sh scripts/run_streamlit.sh [OPTIONS] [-- STREAMLIT_ARGS...]
    (--no-sync keeps a bare `uv run` from re-syncing and stripping the app/retrieval groups)

OPTIONS
    --port N      Port to serve on (default: $SUPPORT_VIEW_PORT or 8501).
    -h, --help    Show this message and exit.

EXAMPLES
    uv run --no-sync sh scripts/run_streamlit.sh                 # serve on :8501
    uv run --no-sync sh scripts/run_streamlit.sh --port 8000     # custom port
    uv run --no-sync sh scripts/run_streamlit.sh -- --server.headless true

PREREQUISITES
    uv sync --group app --group retrieval   # streamlit + live hybrid retrieval
    uv run --no-sync sh scripts/run_ingest.sh   # populates the SQLite store

EXIT CODES
    0   App exited cleanly
    1   Missing dependency or no operational store found
EOF
    exit 0
    ;;
esac

# ── Load project-root .env FIRST (so SUPPORT_VIEW_PORT, OPERATIONAL_STORE, etc. are in
#    scope before we read them below, and reach the app too) ──
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

# ── Argument parsing (a --port flag overrides the .env default) ──────────────────
PORT="${SUPPORT_VIEW_PORT:-8501}"
EXTRA=""
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --) shift; EXTRA="$*"; break ;;
    *) EXTRA="$EXTRA $1"; shift ;;
  esac
done

# ── Dependency check ───────────────────────────────────────────────────────────
uv run --no-sync python3 -c "import streamlit, qdrant_client" 2>/dev/null || {
  echo "App dependencies are missing (streamlit and/or the live-retrieval stack)."
  echo "Install them with: uv sync --group app --group retrieval"
  echo "Then launch with --no-sync so they aren't stripped: uv run --no-sync sh scripts/run_streamlit.sh"
  exit 1
}

# ── Operational store check ────────────────────────────────────────────────────
# the app resolves the DB as $OPERATIONAL_STORE/itsm_rag.db, then the committed
# snapshot at streamlit_app/data/itsm_rag.db.
STORE_DIR="${OPERATIONAL_STORE:-.operational_store}"
if [ ! -f "$STORE_DIR/itsm_rag.db" ] && [ ! -f "streamlit_app/data/itsm_rag.db" ]; then
  echo "No SQLite store found at $STORE_DIR/itsm_rag.db or streamlit_app/data/itsm_rag.db."
  echo "Populate it first: uv run --no-sync sh scripts/run_ingest.sh"
  exit 1
fi

# ── Run ────────────────────────────────────────────────────────────────────────
echo "Starting Streamlit on http://localhost:$PORT  (store: $STORE_DIR)"
exec uv run --no-sync streamlit run streamlit_app/Home.py \
  --server.port "$PORT" --server.fileWatcherType none $EXTRA
