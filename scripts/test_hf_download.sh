#!/usr/bin/env sh
# Download the HF dataset into the cache folder configured in .env (HF_HOME)
# and print absolute file paths for local viewing. Safe to re-run: second
# run is a cache hit. Run from anywhere:  sh scripts/test_hf_download.sh
set -eu

case "${1:-}" in
  -h|--help)
    cat <<'EOF'
Usage: scripts/test_hf_download.sh [--help]

Download (or verify) the HuggingFace dataset snapshot into the local cache
configured in .env (HF_HOME), then print the absolute paths of all expected
files so they can be opened with a local Parquet viewer or editor.

Safe to re-run: subsequent runs are cache hits (no network traffic).

Expected files verified:
  data/train.parquet   745-ticket corpus
  pii.json             PII redaction answer key
  retention.json       Over-redaction answer key

Prerequisites:
  .env                 Must contain HF_HOME (cache dir)
  uv sync              Installs dependencies automatically on first run

Exit codes:
  0  All expected files present in snapshot
  1  One or more files missing
EOF
    exit 0
    ;;
esac

cd "$(dirname "$0")/.."
uv sync -q
uv run python src/test/test_hf_download.py
