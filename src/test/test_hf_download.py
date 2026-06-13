"""Smoke test: download the HF dataset into the cache folder from .env.

Downloads the dataset snapshot (via data_loader, which reads HF_HOME /
HF_TOKEN / dataset repo from .env through config), verifies the expected
files exist, and prints their absolute paths so the parquet can be opened
with a local viewer.

Run via scripts/test_hf_download.sh, or directly:

    uv run python src/test/test_hf_download.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from data_loader import PARQUET_FILENAME, PII_SIDECAR_FILENAME, download_dataset

EXPECTED_FILES = [
    PARQUET_FILENAME,        # data/train.parquet — the 745-ticket corpus
    PII_SIDECAR_FILENAME,    # pii.json — redaction leakage answer key
    "retention.json",        # retention sidecar — over-redaction answer key
]


def main() -> int:
    print(f"dataset repo : {settings.dataset_repo}")
    print(f"cache (HF_HOME from .env): {settings.hf_home.resolve()}")

    snapshot = download_dataset()
    print(f"snapshot dir : {snapshot.resolve()}\n")

    failures = 0
    for rel in EXPECTED_FILES:
        path = snapshot / rel
        if path.exists():
            size_mb = path.stat().st_size / 1e6
            print(f"  OK   {path.resolve()}  ({size_mb:.2f} MB)")
        else:
            print(f"  MISS {rel} — not found in snapshot")
            failures += 1

    if failures:
        print(f"\nFAIL: {failures} expected file(s) missing")
        return 1
    print("\nPASS: snapshot complete. Open the parquet above with your local tool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
