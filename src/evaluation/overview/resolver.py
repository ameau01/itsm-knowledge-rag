"""Store reads for the overview eval — fetch curated_description + ai_overview rows to score.

Mirrors evaluation/curation/resolver.py (store reads kept out of the metric/runner layers).
"""

from __future__ import annotations

import json


def _loads(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def _ticket_count(curated_tickets: str | None) -> int:
    if not curated_tickets:
        return 0
    return len([t for t in str(curated_tickets).split(",") if t.strip()])


def load_eval_cases(conn, *, family=None, root_cause_id=None, heaviest=False,
                    limit=None) -> list[dict]:
    """Raw rows (curated_description + ai_overview + count) for the runner to wrap into cases."""
    rows = conn.execute(
        "SELECT family, root_cause_id, curated_description, curated_tickets, ai_overview "
        "FROM wiki_pages WHERE ai_overview IS NOT NULL AND ai_overview <> '' "
        "ORDER BY family, root_cause_id"
    ).fetchall()
    out = []
    for r in rows:
        if root_cause_id and r["root_cause_id"] != root_cause_id:
            continue
        if family and r["family"] != family:
            continue
        out.append({
            "family": r["family"], "root_cause_id": r["root_cause_id"],
            "curated_description": _loads(r["curated_description"]) or {},
            "ai_overview": _loads(r["ai_overview"]) or {},
            "ticket_count": _ticket_count(r["curated_tickets"]),
        })
    if heaviest:
        out.sort(key=lambda c: c["ticket_count"], reverse=True)
        out = out[:1]
    if limit:
        out = out[:limit]
    return out
