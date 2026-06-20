"""
Corpus reader — the only SQLite touch on the eval path.

Resolves a retrieved point `(ticket_id, section_name)` to its redacted text, and a
ticket id to its root-cause narrative, from the operational store. `SECTION_COLUMNS`
maps the section name a point carries to the `tickets` column that holds its text; this
must match whatever sections the indexer embeds.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from corpus.sections import SECTION_COLUMNS, render_section

# SECTION_COLUMNS + render_section now live in corpus/sections.py (shared with the
# indexer). Re-exported here for backward compatibility — the experiment probes and the
# existing tests import SECTION_COLUMNS from this module.
__all__ = ["CorpusReader", "SECTION_COLUMNS", "render_section"]


def _default_db_path() -> Path:
    try:
        from config import settings  # type: ignore
        return settings.operational_store / "itsm_rag.db"
    except Exception:
        return Path(".operational_store/itsm_rag.db")


class CorpusReader:
    """Read-only reader over the operational store. Use as a context manager or call
    close()."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _default_db_path()
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row

    def section_text(self, ticket_id: str, section_name: str) -> str:
        col = SECTION_COLUMNS.get(section_name)
        if col is None:
            raise KeyError(
                f"unknown section {section_name!r}; known: {sorted(SECTION_COLUMNS)}"
            )
        row = self._conn.execute(
            f"SELECT {col} AS v FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()
        return render_section(row["v"]) if row else ""

    def narratives(self, ticket_ids: Iterable[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        for tid in ticket_ids:
            row = self._conn.execute(
                "SELECT root_cause_narrative AS v FROM tickets WHERE ticket_id = ?", (tid,)
            ).fetchone()
            if row and row["v"]:
                out[tid] = row["v"]
        return out

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "CorpusReader":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
