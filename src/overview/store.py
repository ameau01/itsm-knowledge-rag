"""Overview-specific store reads. 
The canonical wiki_pages CRUD (update_wiki_overview, get_ai_overview, reset_wiki_overview) lives in operational_store.store.
This is just the page selection the generator needs.
"""

from __future__ import annotations

from overview.confidence import ticket_count


def iter_curated_pages(conn, *, family=None, root_cause_id=None, heaviest=False,
                       limit=None) -> list[dict]:
    """Curated pages (curated_description present), filtered/ordered. Raises if none match."""
    rows = conn.execute(
        "SELECT family, root_cause_id, curated_description, curated_tickets "
        "FROM wiki_pages "
        "WHERE curated_description IS NOT NULL AND curated_description <> '' "
        "ORDER BY family, root_cause_id"
    ).fetchall()
    pages = [dict(r) for r in rows]
    if root_cause_id:
        pages = [p for p in pages if p["root_cause_id"] == root_cause_id]
    elif family:
        pages = [p for p in pages if p["family"] == family]
    if heaviest:
        pages.sort(key=lambda p: ticket_count(p["curated_tickets"]), reverse=True)
        pages = pages[:1]
    if limit:
        pages = pages[:limit]
    if not pages:
        raise SystemExit("No curated pages matched the given filters.")
    return pages
