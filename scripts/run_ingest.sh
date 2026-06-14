#!/usr/bin/env sh
# run_ingest.sh — Ingest pipeline: load HF corpus → redact → write to SQLite.
#
# Usage:
#   uv run sh scripts/run_ingest.sh              # ingest all 745 tickets
#   uv run sh scripts/run_ingest.sh --limit 10   # first N tickets (dev/smoke-test)
#   uv run sh scripts/run_ingest.sh --dry-run    # redact only, no DB writes
#   uv run sh scripts/run_ingest.sh --help
#
# Prerequisites:
#   uv sync                                      # installs all dependencies
#   uv run sh scripts/test_hf_download.sh        # downloads corpus + pii.json sidecar
#
# The tickets table is truncated then fully repopulated in a single atomic
# SQLite transaction — a failure mid-run leaves the previous state intact.
#
# Environment:
#   OPERATIONAL_STORE   Path to the SQLite store directory (default: .operational_store)
#   HF_HOME             Path to the HF dataset cache  (default: .hf_cache)
#   PIPELINE_MODE       mock | live                   (default: mock)
# ─────────────────────────────────────────────────────────────────────────────

set -e

# ── Help ───────────────────────────────────────────────────────────────────────
case "${1:-}" in
  -h|--help)
    cat <<'EOF'
run_ingest.sh — Ingest pipeline: load HF corpus → redact → write to SQLite.

USAGE
    uv run sh scripts/run_ingest.sh [OPTIONS]

OPTIONS
    --limit N     Process only the first N tickets. Useful for a quick
                  smoke-test before running the full 745-ticket corpus.
    --dry-run     Redact tickets and report counts but do NOT write to the
                  database. Use this to verify redaction without touching
                  the operational store.
    -h, --help    Show this message and exit.

EXAMPLES
    uv run sh scripts/run_ingest.sh                # full corpus
    uv run sh scripts/run_ingest.sh --limit 5      # smoke-test
    uv run sh scripts/run_ingest.sh --dry-run      # redact only

PREREQUISITES
    uv sync
    uv run sh scripts/test_hf_download.sh

EXIT CODES
    0   Success — all tickets written to DB (or dry-run completed)
    1   Error — missing dependency or runtime failure
EOF
    exit 0
    ;;
esac

# ── Dependency check ───────────────────────────────────────────────────────────
uv run python3 -c "import pandas" 2>/dev/null || {
  echo "Missing Python package: pandas"
  echo "Install with: uv sync"
  exit 1
}

# ── HF cache check ─────────────────────────────────────────────────────────────
HF_CACHE="${HF_HOME:-.hf_cache}"
HF_SNAPSHOTS="$HF_CACHE/datasets--ameau01--synthetic-it-support-tickets/snapshots"

if [ ! -d "$HF_SNAPSHOTS" ] || [ -z "$(ls -A "$HF_SNAPSHOTS" 2>/dev/null)" ]; then
  echo "HF dataset not found at $HF_SNAPSHOTS"
  echo "Downloading now..."
  uv run sh scripts/test_hf_download.sh || {
    echo "Download failed. Run manually: uv run sh scripts/test_hf_download.sh"
    exit 1
  }
fi

# ── Operational store ──────────────────────────────────────────────────────────
# init_db() in store.py creates the DB and tables if they don't exist.
# We just ensure the directory exists here so SQLite can write the file.
STORE_DIR="${OPERATIONAL_STORE:-.operational_store}"
mkdir -p "$STORE_DIR"

# ── Run ────────────────────────────────────────────────────────────────────────
uv run python3 src/ingest/run_ingest.py "$@"
