"""Resolver: read the curation UNDER TEST from wiki_pages, and the SOURCE text from tickets, using the eval recipe only as a formula.
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
RECIPE = _PROJECT / "eval-set" / "wiki" / "wiki-currated-tickets.json"

_ALLOWED_COLUMNS = frozenset(
    {"submitted_description", "correspondence", "root_cause_narrative", "diagnostics_summary"}
)


# ── recipe access (content-free) ─────────────────────────────────────────────────
def load_recipe(path: Path = RECIPE) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def family_records(records: Sequence[dict], family: str) -> list[dict]:
    return [r for r in records if r.get("family") == family]


def members(record: dict) -> list[str]:
    ct = record.get("curated_tickets")
    if isinstance(ct, list):
        return [t for t in ct if t]
    return [t for t in (ct or "").split(",") if t]


# ── store reads: tickets (the SOURCE / ground truth) ─────────────────────────────
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


def recipe_context(conn, record: dict) -> dict[str, list[str]]:
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
    src = record.get("source_sections", {})
    ids = members(record)
    pool: dict[str, list[str]] = {}
    for f in GENERATED_FIELDS:
        texts: list[str] = []
        for col in src.get(f, []):
            texts += _column_texts(conn, ids, col)
        pool[f] = texts
    return pool


# ── store reads: wiki_pages (the curation UNDER TEST) ────────────────────────────
def store_curation(conn, family: str, root_cause_id: str) -> dict:
    row = conn.execute(
        "SELECT curated_description FROM wiki_pages WHERE family = ? AND root_cause_id = ?",
        (family, root_cause_id),
    ).fetchone()
    if row is None or not row[0]:
        return {}
    try:
        data = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def has_curation(curation: dict) -> bool:
    return any((curation.get(f) or "").strip() for f in GENERATED_FIELDS)


def missing_curation(conn, records: Sequence[dict]) -> list[str]:
    return [
        r["root_cause_id"]
        for r in records
        if not has_curation(store_curation(conn, r["family"], r["root_cause_id"]))
    ]


def curation_candidate(conn, record: dict) -> Candidate:
    return Candidate(
        arm="curated",
        root_cause_id=record["root_cause_id"],
        family=record["family"],
        curation=store_curation(conn, record["family"], record["root_cause_id"]),
        context=recipe_context(conn, record),
    )


def page_meta(conn, record: dict) -> PageMeta:
    ids = members(record)
    return PageMeta(
        root_cause_id=record["root_cause_id"],
        n_members=len(ids),
        evidence_pool=evidence_pool(conn, record),
    )


def build_subject(conn, records: Sequence[dict]) -> tuple[list[Candidate], dict[str, PageMeta]]:
    cands = [curation_candidate(conn, r) for r in records]
    meta = {r["root_cause_id"]: page_meta(conn, r) for r in records}
    return cands, meta


def open_store(db: Path | None = None):
    return get_connection(db)
