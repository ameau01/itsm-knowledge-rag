"""
Ingest pipeline: load HF dataset → redact → write to operational store.

For each ticket in the corpus:
  1. Extract text fields from the parquet row
  2. Apply two-layer redaction (sidecar + Presidio)
  3. Write the redacted fields to the SQLite operational store

The full reimport is atomic: the tickets table is truncated and all
inserts happen inside a single SQLite transaction. A failure mid-run
rolls back, leaving the previous complete state intact.

Usage
-----
    uv run python src/ingest/run_ingest.py              # all 745 tickets
    uv run python src/ingest/run_ingest.py --limit 10   # first N tickets (dev)
    uv run python src/ingest/run_ingest.py --dry-run     # redact only, no DB write
    uv run python src/ingest/run_ingest.py --help

Or via the shell wrapper (recommended):
    uv run sh scripts/run_ingest.sh
    uv run sh scripts/run_ingest.sh --limit 10
    uv run sh scripts/run_ingest.sh --dry-run
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
from ingest.redactor import build_sidecar_index, redact_ticket
from ingest.store import (
    count_tickets,
    get_connection,
    init_db,
    insert_redacted_tickets,
    truncate_tks_table,
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


# ── Text extraction (mirrors test_presidio_redaction.py) ──────────────────────

def _to_list(val) -> list:  # type: ignore[type-arg]
    if val is None:
        return []
    if hasattr(val, "tolist"):
        return val.tolist()
    return list(val) if isinstance(val, (list, tuple)) else []


def _str_or_empty(val: object) -> str:
    if val is None or isinstance(val, float):
        return ""
    return str(val)


def _extract_text_fields(row: pd.Series) -> dict[str, str]:  # type: ignore[type-arg]
    parts: dict[str, str] = {}

    ticket = row.get("ticket")
    if isinstance(ticket, dict):
        parts["submitted_description"] = _str_or_empty(
            ticket.get("submitted_description", "")
        )

    corr = _to_list(row.get("correspondence"))
    if corr:
        messages = []
        for c in corr:
            msg = (
                c.get("message", "")
                if hasattr(c, "get")
                else (c._asdict().get("message", "") if hasattr(c, "_asdict") else "")
            )
            if msg:
                messages.append(_str_or_empty(msg))
        parts["correspondence"] = "\n".join(messages)

    diag = row.get("diagnostics")
    if isinstance(diag, dict):
        parts["diagnostics_summary"] = _str_or_empty(diag.get("summary", ""))
        step_texts = []
        for step in _to_list(diag.get("steps")):
            step_d = (
                step._asdict()
                if hasattr(step, "_asdict")
                else (dict(step) if isinstance(step, dict) else {})
            )
            for key in ("description", "expected_result", "observed_result", "evidence"):
                v = step_d.get(key)
                if v:
                    step_texts.append(_str_or_empty(v))
        parts["diagnostics_steps"] = "\n".join(step_texts)

    res = row.get("resolution")
    if isinstance(res, dict):
        parts["resolution_steps"] = "\n".join(
            _str_or_empty(s) for s in _to_list(res.get("steps")) if s
        )
    elif res is not None:
        parts["resolution_steps"] = "\n".join(
            _str_or_empty(s) for s in _to_list(res) if s
        )

    rc = row.get("root_cause")
    if isinstance(rc, dict):
        parts["observations"] = _str_or_empty(rc.get("observations", ""))

    return {k: v for k, v in parts.items() if v}


def _extract_metadata(row: pd.Series) -> dict[str, object]:  # type: ignore[type-arg]
    """Pull family and root_cause_id from the parquet row."""
    family = ""
    root_cause_id = None

    ticket = row.get("ticket")
    if isinstance(ticket, dict):
        family = str(ticket.get("category", "") or "")

    rc = row.get("root_cause")
    if isinstance(rc, dict):
        root_cause_id = rc.get("id") or rc.get("root_cause_id")

    return {"family": family, "root_cause_id": root_cause_id}


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

    # ── Load dataset ───────────────────────────────────────────────────────────
    snap = _ensure_dataset()
    df = pd.read_parquet(snap / "data" / "train.parquet")
    pii_records: list[dict] = json.loads(_find_sidecar("pii.json").read_text())
    sidecar_index = build_sidecar_index(pii_records)

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
        init_db(conn)

    # ── Redact + insert in one transaction ────────────────────────────────────
    t0 = time.monotonic()
    processed = skipped = 0

    if not args.dry_run and conn is not None:
        with conn:                          # atomic: commit on success, rollback on error
            deleted = truncate_tks_table(conn)
            print(f"Cleared {deleted} existing row(s) from tickets table.")

            for tid in ticket_ids:
                rows = df[df["record_id"] == tid]
                if rows.empty:
                    print(f"  SKIP  {tid} — not found in parquet")
                    skipped += 1
                    continue
                row = rows.iloc[0]
                fields = _extract_text_fields(row)
                metadata = _extract_metadata(row)
                redacted = redact_ticket(
                    ticket_id=tid,
                    fields=fields,
                    sidecar_index=sidecar_index,
                    use_presidio_fallback=False,
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
            fields = _extract_text_fields(row)
            redact_ticket(
                ticket_id=tid,
                fields=fields,
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
