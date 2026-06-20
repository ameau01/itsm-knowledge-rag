"""
Section contract — the single source of truth for how a ticket's operational-store
columns become section text.

Shared by both sides of the retrieval system so the text embedded and the text scored are
identical:
  - the indexer / embedder (write path) renders each section to embed it as a point;
  - the evaluation corpus reader (read path) renders the same section to resolve a
    retrieved `(ticket_id, section_name)` point back to its text.

Lives in `corpus` (not `evaluation`) so the production indexer never has to import the
evaluation package. `evaluation/adapter/corpus.py` re-exports `SECTION_COLUMNS` for
backward compatibility.
"""

from __future__ import annotations

import json

# section_name (carried by a retrieved point) -> tickets column holding the redacted text.
SECTION_COLUMNS: dict[str, str] = {
    "description": "submitted_description",
    "correspondence": "correspondence",
    "diagnostics": "diagnostics_procedure",
    "resolution": "resolution_steps",
}

# Stable section order: description, correspondence, diagnostics, resolution.
SECTION_NAMES: tuple[str, ...] = tuple(SECTION_COLUMNS)


def render_section(value: object) -> str:
    """Render a store column value to readable text. JSON-array/object columns
    (diagnostics, resolution) are flattened; plain-text columns pass through.

    The indexer MUST embed this rendered text (not the raw JSON), so the embedded vector
    and the eval-resolved text describe the same thing.
    """
    if value is None:
        return ""
    s = str(value)
    if s[:1] in "[{":
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            return s
        if isinstance(obj, list):
            return "\n".join(render_section(x) for x in obj)
        if isinstance(obj, dict):
            return "; ".join(f"{k}: {v}" for k, v in obj.items())
    return s
