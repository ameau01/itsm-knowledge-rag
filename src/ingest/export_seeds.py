"""Export the operational store into committed SQL seed files — the demo/mock source of truth.

From a curated db, produces:
  db_seeds/tickets.sql          INSERTs for the redacted tickets (data only; schema from store.py)
  db_seeds/curated_content.sql  UPDATE curated_description + curation_details, keyed (family, root_cause_id)
  db_seeds/ai_overview.sql      UPDATE ai_overview + ai_overview_details, keyed (family, root_cause_id)

The two UPDATE files assume the wiki_pages rows already exist (created by seed_wiki_pages); they are
idempotent and order-independent. Re-run whenever you re-curate to refresh the committed seeds.

    uv run sh scripts/export_seeds.sh --db <curated.db> --out db_seeds        # via the wrapper
    uv run --no-sync python3 src/ingest/export_seeds.py --db <db> --out db_seeds  # directly
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def _lit(v: object) -> str:
    """SQLite literal: NULL / number / single-quoted-escaped text."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    s = v if isinstance(v, str) else str(v)
    return "'" + s.replace("'", "''") + "'"


def export_tickets(con: sqlite3.Connection, out: Path) -> int:
    cols = [r[1] for r in con.execute("PRAGMA table_info(tickets)")]
    collist = ", ".join(cols)
    lines = [
        "-- tickets.sql — redacted ticket corpus (DATA ONLY; table created by reset_tickets_table).\n",
        "-- Regenerate with: uv run python3 scripts/export_seeds.py --db <db> --out db_seeds\n",
        "BEGIN;\n",
    ]
    n = 0
    for row in con.execute(f"SELECT {collist} FROM tickets ORDER BY ticket_id"):
        vals = ", ".join(_lit(v) for v in row)
        lines.append(f"INSERT INTO tickets ({collist}) VALUES ({vals});\n")
        n += 1
    lines.append("COMMIT;\n")
    (out / "tickets.sql").write_text("".join(lines), encoding="utf-8")
    return n


def export_updates(con: sqlite3.Connection, out: Path, fname: str,
                   set_cols: list[str], header: str) -> int:
    where = " OR ".join(f"{c} IS NOT NULL" for c in set_cols)
    sel = ", ".join(["family", "root_cause_id", *set_cols])
    lines = [f"-- {fname} — {header}\n", "BEGIN;\n"]
    n = 0
    for row in con.execute(f"SELECT {sel} FROM wiki_pages WHERE {where} "
                           "ORDER BY family, root_cause_id"):
        fam, rc = row[0], row[1]
        sets = ", ".join(f"{c} = {_lit(row[2 + i])}" for i, c in enumerate(set_cols))
        lines.append(
            f"UPDATE wiki_pages SET {sets} WHERE family = {_lit(fam)} "
            f"AND root_cause_id = {_lit(rc)};\n")
        n += 1
    lines.append("COMMIT;\n")
    (out / fname).write_text("".join(lines), encoding="utf-8")
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, required=True, help="source curated db")
    ap.add_argument("--out", type=Path, default=Path("db_seeds"), help="output dir (default: db_seeds)")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(args.db)
    try:
        nt = export_tickets(con, args.out)
        nc = export_updates(con, args.out, "curated_content.sql",
                            ["curated_description", "curation_details"],
                            "UPDATE curated_description + curation_details, keyed (family, root_cause_id)")
        no = export_updates(con, args.out, "ai_overview.sql",
                            ["ai_overview", "ai_overview_details"],
                            "UPDATE ai_overview + ai_overview_details, keyed (family, root_cause_id)")
    finally:
        con.close()
    print(f"tickets.sql: {nt}  curated_content.sql: {nc}  ai_overview.sql: {no}  -> {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
