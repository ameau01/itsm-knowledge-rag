#!/usr/bin/env bash
# Run the Presidio-layer redaction test.
#
# Usage:
#   ./scripts/run_presidio_test.sh                      # sample: first ticket only
#   ./scripts/run_presidio_test.sh --all                # full 745-ticket corpus
#   ./scripts/run_presidio_test.sh --ticket INC-VDA-0001
#   ./scripts/run_presidio_test.sh --verbose            # show retention drops + Presidio hits
#   ./scripts/run_presidio_test.sh --all --verbose
#
# Stdout only. No files written. No operational store touched.
# Exit 0 on pass, 1 on any Gate 1 or Gate 2 failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Help ──────────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'EOF'
Usage: scripts/run_presidio_test.sh [OPTIONS]

Run the two-layer PII redaction test (Layer 1 sidecar + Layer 2 Presidio
pattern recognizers) against the synthetic IT-support ticket corpus.

Modes (mutually exclusive):
  (default)            Test the first ticket only (fast sanity check)
  --all                Test all 745 tickets (full corpus run)
  --ticket ID          Test a single ticket, e.g. --ticket INC-VDA-0001

Options:
  --verbose, -v        Print over-redacted values and surviving Presidio hits
                       per ticket (useful with --all to diagnose retention drops)
  --help, -h           Show this help and exit

Gates:
  Gate 1  ABSENCE-ANYWHERE  [hard fail]   Every pii.json value must be absent
  Gate 2  TOKEN VOCABULARY  [hard fail]   Only the 8 pinned <TOKEN>s may appear
  Gate 3  RETENTION         [report only] ≥0.98 of retention.json values survive

Exit codes:
  0  All hard gates pass
  1  Gate 1 or Gate 2 failure

Prerequisites:
  uv sync          Install dependencies (presidio-analyzer, presidio-anonymizer)
  .env             Must contain HF_HOME and HF_TOKEN (for dataset download)

Examples:
  sh scripts/run_presidio_test.sh
  sh scripts/run_presidio_test.sh --all
  sh scripts/run_presidio_test.sh --ticket INC-VDA-0001
  sh scripts/run_presidio_test.sh --all --verbose
EOF
    exit 0
fi

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
# Pass all arguments directly through to the test script.
PYTHONPATH="$REPO_ROOT/src" uv run python3 "$REPO_ROOT/src/test/test_presidio_redaction.py" "$@"
