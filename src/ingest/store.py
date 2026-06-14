"""
Operational data store — SQLite-backed persistence for the ingest pipeline.

Two tables:
  tickets    Redacted ticket text + structured metadata, one row per source ticket.
             Source of truth for the vector index and serving layer.
  wiki_pages Curated AI-overview per root cause (one row per root_cause_id).
             Populated by the curation step (future); empty after ingest.

Usage
-----
    from ingest.store import get_connection, init_db, insert_redacted_tickets

    conn = get_connection()          # opens / creates the DB
    init_db(conn)                    # creates tables if they don't exist
    truncate_tks_table(conn)         # clear before a full reimport
    insert_redacted_tickets(conn, ticket_id, metadata, redacted_fields, version)
    conn.close()

The caller is responsible for opening and closing the connection.
Transactions are the caller's responsibility too — wrap bulk inserts in
`with conn:` to get atomic commit-or-rollback semantics.
"""

from __future__ import annotations

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
    redacted_at            TEXT    NOT NULL,
    pipeline_version       TEXT    NOT NULL
);
"""

# wiki_pages is populated by the curation step; empty after ingest.
# PK is root_cause_id (not family_id) because each family has multiple root causes.
_DDL_WIKI_PAGES = """
CREATE TABLE IF NOT EXISTS wiki_pages (
    root_cause_id       TEXT    PRIMARY KEY,  -- "AIT/expired-api-token-auth-failures"
    family_id           TEXT    NOT NULL,     -- "AIT"
    family_name         TEXT    NOT NULL,     -- "integration-gateway-api-timeouts"
    issue_statement     TEXT,
    common_symptoms     TEXT,
    root_cause_summary  TEXT,
    resolution_summary  TEXT,
    caveats             TEXT,
    source_ticket_ids   TEXT,                 -- JSON array: ["INC-AIT-0001", ...]
    ticket_count        INTEGER NOT NULL DEFAULT 0,
    curated_at          TEXT,                 -- NULL until curation step runs
    pipeline_version    TEXT,
    curation_model      TEXT                  -- e.g. "claude-haiku-4-5-20251001"
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

    Use this at the start of every ingest run instead of truncate — dropping
    guarantees the live schema always matches the current DDL, preventing silent
    schema-mismatch bugs during refactoring.

    wiki_pages is intentionally NOT touched: it is populated by the separate
    curation step and must survive an ingest re-run.
    """
    conn.execute("DROP TABLE IF EXISTS tickets")
    conn.execute(_DDL_TICKETS)
    conn.commit()


# ── Truncate helpers ───────────────────────────────────────────────────────────

def truncate_tks_table(conn: sqlite3.Connection) -> int:
    """
    Delete all rows from the tickets table (rows only, schema preserved).

    Prefer reset_tickets_table() for full ingest runs — it also refreshes the
    schema.  This helper remains available for targeted row-level resets.

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


# ── Insert ─────────────────────────────────────────────────────────────────────

def insert_redacted_tickets(
    conn: sqlite3.Connection,
    ticket_id: str,
    metadata: dict[str, Any],
    redacted_fields: dict[str, str],
    pipeline_version: str,
) -> None:
    """
    Insert one redacted ticket row into the tickets table.

    Designed to be called inside a `with conn:` transaction block so that a
    failed batch rolls back atomically rather than leaving the table
    half-populated.

    Args:
        conn:             Open SQLite connection (caller manages lifecycle).
        ticket_id:        e.g. "INC-AIT-0001".
        metadata:         Dict from corpus.extractor.extract_metadata(). Keys:
                            family, root_cause_id, submitted_at, priority,
                            sla_plan, environment, applications,
                            diagnostics_coverage
        redacted_fields:  Output of redact_ticket() + observed_errors (not
                          redacted). Expected keys:
                            submitted_description, correspondence,
                            diagnostics_summary, diagnostics_steps,
                            diagnostics_steps_raw, diagnostics_procedure,
                            observed_errors, resolution_steps,
                            root_cause_narrative
        pipeline_version: Semver string, e.g. "0.0.2".
    """
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
            redacted_at, pipeline_version
        ) VALUES (
            :ticket_id, :family, :root_cause_id,
            :submitted_at, :priority, :sla_plan, :environment, :applications,
            :submitted_description, :correspondence,
            :diagnostics_coverage, :diagnostics_summary,
            :diagnostics_steps, :diagnostics_steps_raw, :diagnostics_procedure,
            :observed_errors, :resolution_steps, :root_cause_narrative,
            :redacted_at, :pipeline_version
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
            "redacted_at":            now,
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
