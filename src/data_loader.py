"""Fetch and load the ticket corpus from Hugging Face.

The corpus (ameau01/synthetic-it-support-tickets) is public; no token is
needed. The snapshot is cached under HF_HOME (default .hf_cache/, gitignored);
delete that directory to force a re-download. HF_TOKEN is honored if set,
which lets a private fork of the dataset work unchanged.

Run directly to download and print a schema summary:

    uv run python -m itsm_rag.data_loader
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from huggingface_hub import snapshot_download

from config import settings

PARQUET_FILENAME = "data/train.parquet"
PII_SIDECAR_FILENAME = "pii.json"


def download_dataset(force: bool = False) -> Path:
    """Download the dataset snapshot into the HF_HOME cache.

    Returns the local snapshot directory. Idempotent: a second call is a
    cache hit unless force=True.
    """
    local_dir = snapshot_download(
        repo_id=settings.dataset_repo,
        repo_type="dataset",
        cache_dir=settings.hf_home,
        token=settings.hf_token,
        force_download=force,
    )
    return Path(local_dir)


def load_tickets() -> pd.DataFrame:
    """Load the full ticket corpus as a DataFrame (downloads if needed)."""
    snapshot = download_dataset()
    parquet = snapshot / PARQUET_FILENAME
    if not parquet.exists():
        raise FileNotFoundError(
            f"{PARQUET_FILENAME} not found in snapshot {snapshot}; "
            "the dataset layout may have changed."
        )
    return pd.read_parquet(parquet)


def load_pii_sidecar() -> Any:
    """Load the authored PII ground-truth sidecar (downloads if needed).

    This is the answer key for the deterministic leakage eval. See
    docs/redaction-policy.md for the contract.
    """
    snapshot = download_dataset()
    sidecar = snapshot / PII_SIDECAR_FILENAME
    if not sidecar.exists():
        raise FileNotFoundError(
            f"{PII_SIDECAR_FILENAME} not found in snapshot {snapshot}; "
            "the dataset layout may have changed."
        )
    return json.loads(sidecar.read_text())


def _summarize(df: pd.DataFrame) -> str:
    """Human-readable schema summary, used by the CLI below."""
    lines = [f"records: {len(df)}", "columns:"]
    for col in df.columns:
        dtype = df[col].dtype
        sample = df[col].dropna().iloc[0] if df[col].notna().any() else None
        preview = repr(sample)
        if len(preview) > 80:
            preview = preview[:77] + "..."
        lines.append(f"  {col}  ({dtype})  e.g. {preview}")
    return "\n".join(lines)


if __name__ == "__main__":
    frame = load_tickets()
    print(f"snapshot cached under: {settings.hf_home}")
    print(_summarize(frame))
    sidecar = load_pii_sidecar()
    n = len(sidecar) if isinstance(sidecar, list) else len(sidecar.get("entries", sidecar))
    print(f"pii sidecar: {n} top-level entries")
