"""
Operational data store — SQLite-backed persistence for the ingest pipeline.

Two tables:
  tickets     Redacted ticket text + structured metadata, one row per source ticket. Source of truth for the vector index and serving layer.
  wiki_pages  One row per (family, root_cause_id). The columns (curated_tickets, diagnostic_steps) are filled later by the curation step
  ai_overview A short Google-style summary of the page). Value stay NULL until their generation step runs.

Usage
-----
    from operational_store.store import get_connection, init_db, insert_redacted_tickets

    conn = get_connection() 
    init_db(conn)
    truncate_tks_table(conn)
    insert_redacted_tickets(conn, ticket_id, metadata, redacted_fields, version)
    conn.close()

The caller is responsible for opening and closing the connection. 
DB Transactions are the caller's responsibility to wrap bulk inserts in `with conn:` to get atomic commit-or-rollback semantics.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# ── Schema ─────────────────────────────────────────────────────────────────────

_DDL_TICKETS = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id              TEXT    PRIMARY KEY,
    family                 TEXT    NOT NULL,
    root_cause_id          TEXT,
    -- Ticket metadata (structured, not redacted; used for BM25 filtering)
    submitted_at           TEXT,
    priority               TEXT,
    sla_plan               TEXT,
    environment            TEXT,   -- JSON dict: {os, platform, region, user_group}
    applications           TEXT,   -- JSON array of app name strings
    -- Redacted free-text fields (PII removed; source for embedding + BM25)
    submitted_description  TEXT,
    correspondence         TEXT,
    diagnostics_coverage   TEXT,   -- 'standard' / 'extended' / etc.
    diagnostics_summary    TEXT,
    diagnostics_steps      TEXT,   -- JSON array: canonical steps (playbook_step_id,
                                   --   expected_result, result_status, performed_by)
                                   --   cardinality contract: 365 unique step-sets
    diagnostics_steps_raw  TEXT,   -- JSON array: all 8 fields incl. action /
                                   --   observed_result / evidence; L1 context + retention
    diagnostics_procedure  TEXT,   -- JSON array: {step, action, expected_result};
                                   --   lean input for wiki generator LLM
    observed_errors        TEXT,   -- JSON array of error codes (not redacted)
    resolution_steps       TEXT,   -- JSON array of resolution step strings
    root_cause_narrative   TEXT,   -- engineer's causal summary (root_cause column)
    -- Pipeline bookkeeping
    upserted_at            TEXT    NOT NULL,   -- when this row was last written
    pipeline_version       TEXT    NOT NULL
);
"""

# wiki_pages: one row per (family, root_cause_id). 
_DDL_WIKI_PAGES = """
CREATE TABLE IF NOT EXISTS wiki_pages (
    family              TEXT    NOT NULL,
    root_cause_id       TEXT    NOT NULL,
    curated_description TEXT,                 -- JSON {title,symptoms,cause,variations,reporting}; NULL until curated
    diagnostic_steps    TEXT,                 -- JSON [{step,action,expected_result}]; canonical playbook (ingest)
    curated_tickets     TEXT,                 -- comma-joined member ticket_ids (ingest)
    curation_details    TEXT,                 -- JSON {model,pipeline_version,curated_at}; NULL until curated
    ai_overview         TEXT,                 -- JSON {lead,key_points,confidence,evidence}; NULL until overview generated
    ai_overview_details TEXT,                 -- JSON {model,pipeline_version,generated_at}; NULL until overview generated
    upserted_at         TEXT    NOT NULL,     -- seeded by ingest, bumped by curation load
    PRIMARY KEY (family, root_cause_id)
);
"""


# ── Connection ─────────────────────────────────────────────────────────────────

def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Open (or create) the SQLite database.

    Args:
        db_path: explicit path to the .db file. Defaults to
                 settings.operational_store / "itsm_rag.db".

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    if db_path is None:
        store_dir = settings.operational_store
        store_dir.mkdir(parents=True, exist_ok=True)
        db_path = store_dir / "itsm_rag.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema initialisation ──────────────────────────────────────────────────────

def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't already exist. Idempotent."""
    conn.execute(_DDL_TICKETS)
    conn.execute(_DDL_WIKI_PAGES)
    conn.commit()


def reset_tickets_table(conn: sqlite3.Connection) -> None:
    """
    Drop and recreate the tickets table.

    """
    conn.execute("DROP TABLE IF EXISTS tickets")
    conn.execute(_DDL_TICKETS)
    conn.commit()


# ── Truncate helpers ───────────────────────────────────────────────────────────

def truncate_tks_table(conn: sqlite3.Connection) -> int:
    """
    Delete all rows from the tickets table (rows only, schema preserved).

    Returns:
        Number of rows deleted.
    """
    cur = conn.execute("DELETE FROM tickets")
    return cur.rowcount


def truncate_wiki_table(conn: sqlite3.Connection) -> int:
    """
    Delete all rows from the wiki_pages table.

    Returns:
        Number of rows deleted.
    """
    cur = conn.execute("DELETE FROM wiki_pages")
    return cur.rowcount


def reset_wiki_pages(conn: sqlite3.Connection) -> None:
    """Drop and recreate wiki_pages with the current schema (called by ingest before seeding)."""
    conn.execute("DROP TABLE IF EXISTS wiki_pages")
    conn.execute(_DDL_WIKI_PAGES)
    conn.commit()


def seed_wiki_pages(conn: sqlite3.Connection) -> int:
    """
    Seed one wiki_pages row per (family, root_cause_id).

    Returns:
        Number of wiki_pages rows seeded.
    """
    from operational_store.diagnostics import canonical_diagnostic_steps

    now = datetime.now(timezone.utc).isoformat()
    groups = conn.execute(
        "SELECT DISTINCT family, root_cause_id FROM tickets "
        "WHERE root_cause_id IS NOT NULL ORDER BY family, root_cause_id"
    ).fetchall()
    for g in groups:
        members = [
            r[0] for r in conn.execute(
                "SELECT ticket_id FROM tickets WHERE root_cause_id = ? ORDER BY ticket_id",
                (g["root_cause_id"],),
            )
        ]
        steps = canonical_diagnostic_steps(conn, g["root_cause_id"])
        conn.execute(
            "INSERT OR REPLACE INTO wiki_pages "
            "(family, root_cause_id, curated_tickets, diagnostic_steps, upserted_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (g["family"], g["root_cause_id"], ",".join(members),
             json.dumps(steps, ensure_ascii=False), now),
        )
    conn.commit()
    return len(groups)


def update_wiki_curation(
    conn: sqlite3.Connection,
    family: str,
    root_cause_id: str,
    curated_description: str,
    curation_details: str,
) -> int:
    """
    Curation load writes ONLY the generated columns (curated_description, curation_details).

    Returns:
        Number of rows updated (1 if the page exists, 0 otherwise).
    """
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "UPDATE wiki_pages SET curated_description = ?, curation_details = ?, upserted_at = ? "
        "WHERE family = ? AND root_cause_id = ?",
        (curated_description, curation_details, now, family, root_cause_id),
    )
    return cur.rowcount


# ── Insert ─────────────────────────────────────────────────────────────────────

def insert_redacted_tickets(
    conn: sqlite3.Connection,
    ticket_id: str,
    metadata: dict[str, Any],
    redacted_fields: dict[str, str],
    pipeline_version: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT OR REPLACE INTO tickets (
            ticket_id, family, root_cause_id,
            submitted_at, priority, sla_plan, environment, applications,
            submitted_description, correspondence,
            diagnostics_coverage, diagnostics_summary,
            diagnostics_steps, diagnostics_steps_raw, diagnostics_procedure,
            observed_errors, resolution_steps, root_cause_narrative,
            upserted_at, pipeline_version
        ) VALUES (
            :ticket_id, :family, :root_cause_id,
            :submitted_at, :priority, :sla_plan, :environment, :applications,
            :submitted_description, :correspondence,
            :diagnostics_coverage, :diagnostics_summary,
            :diagnostics_steps, :diagnostics_steps_raw, :diagnostics_procedure,
            :observed_errors, :resolution_steps, :root_cause_narrative,
            :upserted_at, :pipeline_version
        )
        """,
        {
            "ticket_id":              ticket_id,
            "family":                 metadata.get("family", ""),
            "root_cause_id":          metadata.get("root_cause_id"),
            "submitted_at":           metadata.get("submitted_at"),
            "priority":               metadata.get("priority"),
            "sla_plan":               metadata.get("sla_plan"),
            "environment":            metadata.get("environment"),
            "applications":           metadata.get("applications"),
            "submitted_description":  redacted_fields.get("submitted_description"),
            "correspondence":         redacted_fields.get("correspondence"),
            "diagnostics_coverage":   metadata.get("diagnostics_coverage"),
            "diagnostics_summary":    redacted_fields.get("diagnostics_summary"),
            "diagnostics_steps":      redacted_fields.get("diagnostics_steps"),
            "diagnostics_steps_raw":  redacted_fields.get("diagnostics_steps_raw"),
            "diagnostics_procedure":  redacted_fields.get("diagnostics_procedure"),
            "observed_errors":        redacted_fields.get("observed_errors"),
            "resolution_steps":       redacted_fields.get("resolution_steps"),
            "root_cause_narrative":   redacted_fields.get("root_cause_narrative"),
            "upserted_at":            now,
            "pipeline_version":       pipeline_version,
        },
    )


# ── Query helpers (used by retrieval / serving layer) ─────────────────────────

def get_ticket(conn: sqlite3.Connection, ticket_id: str) -> sqlite3.Row | None:
    """Fetch a single redacted ticket by ID."""
    cur = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    return cur.fetchone()


def get_tickets_by_family(conn: sqlite3.Connection, family: str) -> list[sqlite3.Row]:
    """Fetch all redacted tickets for an issue family."""
    cur = conn.execute(
        "SELECT * FROM tickets WHERE family = ? ORDER BY ticket_id", (family,)
    )
    return cur.fetchall()


def get_tickets_by_root_cause(
    conn: sqlite3.Connection, root_cause_id: str
) -> list[sqlite3.Row]:
    """Fetch all redacted tickets for a specific root cause."""
    cur = conn.execute(
        "SELECT * FROM tickets WHERE root_cause_id = ? ORDER BY ticket_id",
        (root_cause_id,),
    )
    return cur.fetchall()


def count_tickets(conn: sqlite3.Connection) -> int:
    """Return total number of redacted tickets in the store."""
    cur = conn.execute("SELECT COUNT(*) FROM tickets")
    row = cur.fetchone()
    return row[0] if row else 0


def get_wiki_page(conn: sqlite3.Connection, root_cause_id: str) -> sqlite3.Row | None:
    """Fetch the curated wiki page for a root cause."""
    cur = conn.execute(
        "SELECT * FROM wiki_pages WHERE root_cause_id = ?", (root_cause_id,)
    )
    return cur.fetchone()


# ── AI overview (query-time L2 selection support) ───────────────────────────────

_OVERVIEW_SECTIONS = ("description", "correspondence", "diagnostics", "resolution")


def _wiki_has_column(conn: sqlite3.Connection, col: str) -> bool:
    return any(r[1] == col for r in conn.execute("PRAGMA table_info(wiki_pages)"))


def _overview_loads(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def get_ai_overview(conn: sqlite3.Connection, root_cause_id: str) -> dict | None:
    """The chosen page's AI overview + curated/diagnostic payload for the serving layer, or None.
    """
    if not _wiki_has_column(conn, "ai_overview"):
        return None
    row = conn.execute(
        "SELECT family, root_cause_id, ai_overview, ai_overview_details, "
        "curated_description, diagnostic_steps, curated_tickets "
        "FROM wiki_pages WHERE root_cause_id = ?",
        (root_cause_id,),
    ).fetchone()
    if row is None or not (row["ai_overview"] or "").strip():
        return None
    overview = _overview_loads(row["ai_overview"])
    if not isinstance(overview, dict):
        return None
    return {
        "family": row["family"], "root_cause_id": row["root_cause_id"],
        "ai_overview": overview,
        "ai_overview_details": _overview_loads(row["ai_overview_details"]),
        "curated_description": _overview_loads(row["curated_description"]),
        "diagnostic_steps": _overview_loads(row["diagnostic_steps"]),
        "curated_tickets": row["curated_tickets"],
    }


def build_card_lookup(conn: sqlite3.Connection) -> dict:
    """(ticket_id, section_name) -> {'family', 'root_cause'(slug)} for every ticket × section.
    """
    rows = conn.execute("SELECT ticket_id, family, root_cause_id FROM tickets").fetchall()
    lookup = {}
    for r in rows:
        rc = r["root_cause_id"]
        card = {"family": r["family"], "root_cause": rc.split("/", 1)[-1] if rc else None}
        for sec in _OVERVIEW_SECTIONS:
            lookup[(r["ticket_id"], sec)] = card
    return lookup
