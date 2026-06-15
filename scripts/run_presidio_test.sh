#!/usr/bin/env sh
# Run the full three-layer redaction test (L1+L2+L3 Presidio).
#
# Usage:
#   uv run sh scripts/run_presidio_test.sh                      # sample: first ticket only
#   uv run sh scripts/run_presidio_test.sh --all                # full 745-ticket corpus
#   uv run sh scripts/run_presidio_test.sh --ticket INC-VDA-0001
#   uv run sh scripts/run_presidio_test.sh --verbose
#
# Stdout only. No files written. No operational store touched.
# Exit 0 on pass, 1 on any Gate 1 or Gate 2 failure.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

case "${1:-}" in
  -h|--help)
    cat <<'EOF'
Usage: scripts/run_presidio_test.sh [OPTIONS]

Run the full three-layer PII redaction test (AD identity + format rules +
Presidio NER) against the synthetic IT-support ticket corpus.

Modes (mutually exclusive):
  (default)            Test the first ticket only (fast sanity check)
  --all                Test all 745 tickets (full corpus run)
  --ticket ID          Test a single ticket, e.g. --ticket INC-VDA-0001

Options:
  --verbose, -v        Print over-redacted values and surviving Presidio hits
  --help, -h           Show this help and exit

Gates:
  Gate 1  ABSENCE-ANYWHERE  [hard fail]   Every pii.json value must be absent
  Gate 2  TOKEN VOCABULARY  [hard fail]   Only the 8 pinned <TOKEN>s may appear
  Gate 3  RETENTION         [report only] target >= 0.98

Exit codes:
  0  All hard gates pass
  1  Gate 1 or Gate 2 failure

Prerequisites:
  uv sync
  uv run sh scripts/test_hf_download.sh

Examples:
  uv run sh scripts/run_presidio_test.sh
  uv run sh scripts/run_presidio_test.sh --all
  uv run sh scripts/run_presidio_test.sh --ticket INC-VDA-0001
  uv run sh scripts/run_presidio_test.sh --all --verbose
EOF
    exit 0
    ;;
esac

# ── Dependency check ──────────────────────────────────────────────────────────
check_dep() {
    uv run python3 -c "import $1" 2>/dev/null || {
        echo "Missing Python package: $1"
        echo "Install with: uv sync"
        exit 1
    }
}
check_dep presidio_analyzer
check_dep presidio_anonymizer
check_dep pandas
check_dep yaml

# ── Run ───────────────────────────────────────────────────────────────────────
PYTHONPATH="$REPO_ROOT/src" uv run python3 "$REPO_ROOT/src/test/test_presidio_redaction.py" "$@"
