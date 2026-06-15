#!/usr/bin/env sh
# score_redaction.sh
#
# Usage:
#   uv run sh scripts/score_redaction.sh                    # all 745 tickets
#   uv run sh scripts/score_redaction.sh --family AIT       # single family
#   uv run sh scripts/score_redaction.sh --no-presidio      # L1+L2 only
#   uv run sh scripts/score_redaction.sh --help
#
# Scores PolicyRedactor against:
#   pii.json       — REMOVE answer key (PII recall)
#   retention.json — KEEP answer key   (retention / over-redaction)
#
# Prerequisites:
#   uv sync
#   uv run sh scripts/test_hf_download.sh   (downloads corpus + sidecars)
# ─────────────────────────────────────────────────────────────────────────────

set -e

case "${1:-}" in
  -h|--help)
    cat <<'EOF'
score_redaction.sh

USAGE
    uv run sh scripts/score_redaction.sh [OPTIONS]

OPTIONS
    --family FAMILY   Score a single ticket family (AIT, ALP, CES, DCP, DRF,
                      EDE, LPD, OES, PDQ, SDA, SIB, SML, VDA, WCI) or ALL
                      (default: ALL).
    --no-presidio     Disable Layer 3 Presidio NER — score L1+L2 only.
    -h, --help        Show this message and exit.

EXAMPLES
    uv run sh scripts/score_redaction.sh                   # full corpus
    uv run sh scripts/score_redaction.sh --family AIT      # one family
    uv run sh scripts/score_redaction.sh --no-presidio     # AD+rules only

PREREQUISITES
    uv sync
    uv run sh scripts/test_hf_download.sh
EOF
    exit 0
    ;;
esac

HF_CACHE="${HF_HOME:-.hf_cache}"
HF_SNAPSHOTS="$HF_CACHE/datasets--ameau01--synthetic-it-support-tickets/snapshots"

if [ ! -d "$HF_SNAPSHOTS" ] || [ -z "$(ls -A "$HF_SNAPSHOTS" 2>/dev/null)" ]; then
  echo "HF dataset not found. Run: uv run sh scripts/test_hf_download.sh"
  exit 1
fi

uv run python3 src/ingest/score.py "$@"
