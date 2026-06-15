#!/usr/bin/env sh
# run_extraction_test.sh — Oracle tests for corpus extraction correctness.
#
# Tests (src/test/test_extraction.py):
#   1. family        non-empty, equals record_id.split('-')[1]
#   2. root_cause_id non-null, from catalog.json inversion
#   3. root_cause_narrative  present in extract_text_fields()
#   4. observed_errors       non-empty for tickets with diagnostic errors
#   5. diag_cardinality      unique step-sets per root_cause_id match
#                            corpus-cardinality.xlsx for all 76 root causes
#
# Usage:
#   uv run sh scripts/run_extraction_test.sh
#   uv run sh scripts/run_extraction_test.sh --help
#
# Prerequisites:
#   uv sync
#   uv run sh scripts/test_hf_download.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

case "${1:-}" in
  -h|--help)
    cat <<'EOF'
run_extraction_test.sh — Oracle tests for corpus extraction correctness.

USAGE
    uv run sh scripts/run_extraction_test.sh [PYTEST_ARGS]

TESTS
    test_family_non_empty          family = record_id.split('-')[1]
    test_root_cause_id_non_null    root_cause_id from catalog.json
    test_root_cause_narrative_present  root_cause string stored as narrative
    test_observed_errors_extracted  diagnostics.observed_errors extracted
    test_diag_cardinality          unique step-sets match cardinality spreadsheet

EXAMPLES
    uv run sh scripts/run_extraction_test.sh
    uv run sh scripts/run_extraction_test.sh -v
    uv run sh scripts/run_extraction_test.sh -k test_diag_cardinality

PREREQUISITES
    uv sync
    uv run sh scripts/test_hf_download.sh

EXIT CODES
    0   All oracle tests pass 
    1   One or more tests fail
EOF
    exit 0
    ;;
esac

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

uv run python -m pytest src/test/test_extraction.py -v "$@"
