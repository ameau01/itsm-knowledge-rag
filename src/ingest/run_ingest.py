"""
Ingest pipeline: load HF dataset → redact → write to operational store.

For each ticket in the corpus:
  1. Extract text fields (corpus.extractor)
  2. Extract structured metadata (corpus.extractor + corpus.catalog)
  3. Apply two-layer PII redaction (sidecar + Presidio)
  4. Write to SQLite operational store (ingest.store)

The full reimport is atomic: the tickets table is truncated and all inserts
happen inside a single SQLite transaction.  A failure mid-run rolls back,
leaving the previous complete state intact.

Usage
-----
    uv run sh scripts/run_ingest.sh              # all 745 tickets
    uv run sh scripts/run_ingest.sh --limit 10   # first N tickets (dev)
    uv run sh scripts/run_ingest.sh --dry-run    # redact only, no DB write
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from corpus.catalog import build_rc_map
from corpus.extractor import (
    extract_metadata,
    extract_observed_errors,
    extract_text_fields,
)
from ingest.redactor import build_sidecar_index, redact_ticket
from ingest.store import (
    count_tickets,
    get_connection,
    insert_redacted_tickets,
    reset_tickets_table,
)

# ── Constants ──────────────────────────────────────────────────────────────────

_PIPELINE_VERSION = "0.0.2"   # keep in sync with pyproject.toml

_HF_CACHE = Path(__file__).parent.parent.parent / ".hf_cache"
_SNAPSHOTS = (
    _HF_CACHE
    / "datasets--ameau01--synthetic-it-support-tickets"
    / "snapshots"
)
_EVAL_REDACTION = Path(__file__).parent.parent.parent / "eval-set" / "redaction"


# ── Dataset helpers ────────────────────────────────────────────────────────────

def _latest_snapshot() -> Path | None:
    if not _SNAPSHOTS.exists():
        return None
    snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return snaps[0] if snaps else None


def _ensure_dataset() -> Path:
    snap = _latest_snapshot()
    if snap and (snap / "data" / "train.parquet").exists():
        return snap
    print("HF snapshot not found — downloading …")
    from data_loader import download_dataset
    return download_dataset()


def _find_sidecar(filename: str) -> Path:
    local = _EVAL_REDACTION / filename
    if local.exists():
        return local
    snap = _latest_snapshot()
    if snap:
        candidate = snap / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"{filename} not found in {_EVAL_REDACTION} or HF cache.\n"
        "Run: uv run sh scripts/test_hf_download.sh"
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest pipeline: load the HF ticket corpus, apply two-layer PII "
            "redaction, and write redacted tickets to the SQLite operational store. "
            "The tickets table is truncated then fully repopulated in one atomic "
            "transaction — a failure mid-run leaves the previous state intact."
        ),
        epilog=(
            "DB location: $OPERATIONAL_STORE/itsm_rag.db  "
            "(default: .operational_store/itsm_rag.db). "
            "Configure via .env or the OPERATIONAL_STORE env var."
        ),
    )
    parser.add_argument(
        "--limit",
        metavar="N",
        type=int,
        default=None,
        help="Process only the first N tickets (useful for dev/smoke-test).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Redact tickets and report counts but do NOT write to the database. "
            "Useful for verifying redaction without touching the store."
        ),
    )
    args = parser.parse_args(argv)

    # ── Load dataset and lookup maps ───────────────────────────────────────────
    snap = _ensure_dataset()
    df = pd.read_parquet(snap / "data" / "train.parquet")
    pii_records: list[dict] = json.loads(_find_sidecar("pii.json").read_text())
    sidecar_index = build_sidecar_index(pii_records)
    rc_map = build_rc_map()  # ticket_id → root_cause_id from catalog.json

    ticket_ids: list[str] = df["record_id"].tolist()
    if args.limit:
        ticket_ids = ticket_ids[: args.limit]

    total = len(ticket_ids)
    label = f"first {total}" if args.limit else f"all {total}"
    mode = "DRY RUN — no DB writes" if args.dry_run else f"→ {settings.operational_store}"
    print(f"\nIngest pipeline  |  {label} ticket(s)  |  {mode}")
    print(f"Sidecar : {_find_sidecar('pii.json')}")
    print(f"Version : {_PIPELINE_VERSION}\n")

    # ── Open DB (skip if dry-run) ──────────────────────────────────────────────
    conn = None
    if not args.dry_run:
        conn = get_connection()
        # Drop and recreate tickets table so the live schema always matches the
        # current DDL — prevents silent schema-mismatch bugs during refactoring.
        # wiki_pages is left intact (populated by the separate curation step).
        reset_tickets_table(conn)
        print("Tickets table reset (dropped + recreated with current schema).")

    # ── Redact + insert in one transaction ────────────────────────────────────
    t0 = time.monotonic()
    processed = skipped = 0

    if not args.dry_run and conn is not None:
        with conn:                          # atomic: commit on success, rollback on error

            for tid in ticket_ids:
                rows = df[df["record_id"] == tid]
                if rows.empty:
                    print(f"  SKIP  {tid} — not found in parquet")
                    skipped += 1
                    continue
                row = rows.iloc[0]

                # Extract text fields (redactable) and metadata (not redacted)
                text_fields = extract_text_fields(row)
                metadata = extract_metadata(row, rc_map)
                observed_errors = extract_observed_errors(row)

                # Apply PII redaction to text fields
                redacted = redact_ticket(
                    ticket_id=tid,
                    fields=text_fields,
                    sidecar_index=sidecar_index,
                    use_presidio_fallback=False,
                )

                # Merge observed_errors (not redacted) into the redacted dict
                if observed_errors:
                    redacted["observed_errors"] = json.dumps(
                        observed_errors, ensure_ascii=False
                    )

                insert_redacted_tickets(conn, tid, metadata, redacted, _PIPELINE_VERSION)
                processed += 1
    else:
        # Dry run: redact only, no DB writes
        for tid in ticket_ids:
            rows = df[df["record_id"] == tid]
            if rows.empty:
                skipped += 1
                continue
            row = rows.iloc[0]
            text_fields = extract_text_fields(row)
            redact_ticket(
                ticket_id=tid,
                fields=text_fields,
                sidecar_index=sidecar_index,
                use_presidio_fallback=False,
            )
            processed += 1

    elapsed = time.monotonic() - t0

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'─' * 56}")
    print(f"Processed : {processed} ticket(s)")
    if skipped:
        print(f"Skipped   : {skipped} (not found in parquet)")
    print(f"Elapsed   : {elapsed:.1f}s")

    if not args.dry_run and conn is not None:
        db_count = count_tickets(conn)
        conn.close()
        print(f"DB rows   : {db_count} in tickets table")
        print(f"DB path   : {settings.operational_store / 'itsm_rag.db'}")

    print(f"{'─' * 56}")
    print("DONE" if not args.dry_run else "DRY RUN complete — database unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
