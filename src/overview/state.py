"""TypedDict state for the overview agent. One state = one (family, root_cause_id) page.
"""

from __future__ import annotations

from typing import TypedDict


class OverviewState(TypedDict, total=False):
    # fixed per page (inputs)
    family: str
    root_cause_id: str
    curated: dict            # the curated_description fields
    ticket_count: int
    nature: str              # confirmed | unconfirmed
    confidence: str          # high | medium | low (computed before the agent)
    # output
    lead: str
    key_points: list[str]
