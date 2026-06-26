"""Curation loader: curation-output files -> wiki_pages.curated_description.

Reads the external generation step's output (one curation file per root cause) and
writes ONLY the generated columns (curated_description, curation_details) into wiki_pages,
bumping upserted_at. The deterministic columns (diagnostic_steps, curated_tickets) are
ingest's and are left untouched.

Handoff contract (the only shape this depends on):
    { "root_cause_id", "family", "source_ticket_ids": [...],
      "curation": { "title","symptoms","cause","variations","diagnostic_summary","reporting" } }

Run:
    python -m wiki.load --curation-dir <dir> [--db <path>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # put src/ on the path
from operational_store.store import get_connection, update_wiki_curation  # noqa: E402

_CURATED_KEYS = ["title", "symptoms", "cause", "variations", "diagnostic_summary", "reporting"]


def load(conn, curation_dir: Path) -> tuple[int, int]:
    """Apply every curation file under curation_dir. Returns (applied, missing_page)."""
    applied = missing = 0
    for jf in sorted(Path(curation_dir).glob("*/*.curation.json")):
        rec = json.loads(jf.read_text(encoding="utf-8"))
        u = rec.get("curation", {})
        curated_description = json.dumps(
            {k: (u.get(k) or "") for k in _CURATED_KEYS}, ensure_ascii=False
        )
        curation_details = json.dumps(
            {
                "model": rec.get("curation_model"),
                "pipeline_version": rec.get("pipeline_version"),
                "curated_at": rec.get("curated_at"),
            },
            ensure_ascii=False,
        )
        n = update_wiki_curation(
            conn, rec["family"], rec["root_cause_id"], curated_description, curation_details
        )
        if n:
            applied += 1
        else:
            missing += 1
            print(f"  WARN  no wiki_pages row for {rec['root_cause_id']} (ingest first?)")
    conn.commit()
    return applied, missing


def integrity(conn) -> tuple[int, int, int]:
    """Every curated_tickets member must exist in tickets and share its page's root_cause_id.
    Returns (member_links, missing, mismatch)."""
    links = missing = mismatch = 0
    for _fam, rc, ct in conn.execute(
        "SELECT family, root_cause_id, curated_tickets FROM wiki_pages"
    ):
        for tid in (ct or "").split(","):
            if not tid:
                continue
            links += 1
            row = conn.execute(
                "SELECT root_cause_id FROM tickets WHERE ticket_id = ?", (tid,)
            ).fetchone()
            if row is None:
                missing += 1
            elif row[0] != rc:
                mismatch += 1
    return links, missing, mismatch


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--curation-dir", required=True, type=Path)
    ap.add_argument("--db", type=Path, help="explicit DB path (default: settings.operational_store)")
    args = ap.parse_args()

    conn = get_connection(args.db)
    applied, missing_page = load(conn, args.curation_dir)
    rows = conn.execute("SELECT COUNT(*) FROM wiki_pages").fetchone()[0]
    curated = conn.execute(
        "SELECT COUNT(*) FROM wiki_pages WHERE curated_description IS NOT NULL"
    ).fetchone()[0]
    links, missing, mismatch = integrity(conn)
    conn.close()

    print(f"applied {applied} curation file(s) ({missing_page} with no matching page)")
    print(f"wiki_pages: {rows} rows, {curated} curated")
    print(f"integrity: {links} member links, {missing} missing, {mismatch} mismatch")
    if missing or mismatch:
        sys.exit("INTEGRITY FAILURE")


if __name__ == "__main__":
    main()
