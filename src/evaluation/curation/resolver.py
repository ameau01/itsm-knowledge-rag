"""Resolver: turn the eval mapping's logical ids into reference text from the store.

The eval file (eval-set/wiki/wiki-currated-tickets.json) names ticket_ids and column names
only — never table internals. This module is the one place that reads the operational store,
so the eval file stays storage-agnostic. All reads are in-project (the operational store +
the in-project eval mapping); nothing here references the parent or experiment folders.

Two reference views (the "split" decision):
  - gold_context(): per generated field, EXACTLY what the gold generation saw — honoring
    `deduplicated` (root_cause_narrative) and `capped_at` (diagnostics_summary). This becomes
    the gold arm's per-arm faithfulness context.
  - evidence_pool(): per field, ALL member tickets' source columns, uncapped and undeduped —
    the completeness reference for summarization / variation.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/ on the path
from operational_store.store import get_connection  # noqa: E402

from .contracts import GENERATED_FIELDS, Candidate, PageMeta  # noqa: E402

_PROJECT = Path(__file__).resolve().parents[3]
GOLD = _PROJECT / "eval-set" / "wiki" / "wiki-currated-tickets.json"

# Only these ticket columns may feed curation; an allowlist keeps the SELECT injection-safe
# (column names arrive from the eval file's source_sections).
_ALLOWED_COLUMNS = frozenset(
    {"submitted_description", "correspondence", "root_cause_narrative", "diagnostics_summary"}
)


# ── eval-file access ───────────────────────────────────────────────────────────────
def load_gold(path: Path = GOLD) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def family_records(records: Sequence[dict], family: str) -> list[dict]:
    return [r for r in records if r.get("family") == family]


def members(record: dict) -> list[str]:
    ct = record.get("curated_tickets")
    if isinstance(ct, list):
        return [t for t in ct if t]
    return [t for t in (ct or "").split(",") if t]


# ── store reads ────────────────────────────────────────────────────────────────────
def _column_texts(
    conn,
    ticket_ids: Sequence[str],
    column: str,
    *,
    deduplicated: bool = False,
    capped_at: int | None = None,
) -> list[str]:
    if column not in _ALLOWED_COLUMNS:
        raise ValueError(f"column not allowed as curation input: {column!r}")
    ids = list(ticket_ids)[:capped_at] if capped_at else list(ticket_ids)
    out: list[str] = []
    for tid in ids:
        row = conn.execute(
            f"SELECT {column} FROM tickets WHERE ticket_id = ?", (tid,)  # noqa: S608 (allowlisted)
        ).fetchone()
        if row is None or row[0] is None:
            continue
        val = row[0]
        out.append(val if isinstance(val, str) else json.dumps(val, ensure_ascii=False))
    if deduplicated:
        out = list(dict.fromkeys(out))
    return out


def gold_context(conn, record: dict) -> dict[str, list[str]]:
    """Per generated field: exactly what the gold generation saw (source_sections columns
    resolved over input_scope ids, honoring deduplicated / capped_at)."""
    src = record.get("source_sections", {})
    scope = record.get("input_scope", {})
    ctx: dict[str, list[str]] = {}
    for f in GENERATED_FIELDS:
        texts: list[str] = []
        for col in src.get(f, []):
            info = scope.get(col, {})
            texts += _column_texts(
                conn,
                info.get("ticket_ids", []),
                col,
                deduplicated=bool(info.get("deduplicated", False)),
                capped_at=info.get("capped_at"),
            )
        ctx[f] = texts
    return ctx


def evidence_pool(conn, record: dict) -> dict[str, list[str]]:
    """Per generated field: ALL member tickets' source columns, uncapped and undeduped."""
    src = record.get("source_sections", {})
    ids = members(record)
    pool: dict[str, list[str]] = {}
    for f in GENERATED_FIELDS:
        texts: list[str] = []
        for col in src.get(f, []):
            texts += _column_texts(conn, ids, col)
        pool[f] = texts
    return pool


def synthesize_gold_candidate(conn, record: dict) -> Candidate:
    """The human-curated gold as the first arm: its output is curated_description, its
    per-field context is exactly the gold input_scope."""
    return Candidate(
        arm="gold",
        root_cause_id=record["root_cause_id"],
        family=record["family"],
        curation=record["curated_description"],
        context=gold_context(conn, record),
    )


def page_meta(conn, record: dict) -> PageMeta:
    ids = members(record)
    return PageMeta(
        root_cause_id=record["root_cause_id"],
        n_members=len(ids),
        evidence_pool=evidence_pool(conn, record),
    )


def build_gold_arm(conn, records: Sequence[dict]) -> tuple[list[Candidate], dict[str, PageMeta]]:
    """Convenience: the gold arm's candidates + per-page meta for a set of records."""
    cands = [synthesize_gold_candidate(conn, r) for r in records]
    meta = {r["root_cause_id"]: page_meta(conn, r) for r in records}
    return cands, meta


def open_store(db: Path | None = None):
    """Open the in-project operational store (default path from settings)."""
    return get_connection(db)
