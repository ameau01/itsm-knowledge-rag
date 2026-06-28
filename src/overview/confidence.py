"""Deterministic confidence — computed BEFORE the agent call so it shapes the prompt hedge.

Pure logic, no deps. Locked rule: a low-trust slug forces `low` regardless of ticket count;
otherwise >=10 high, 3-9 medium, <=2 low.
"""

from __future__ import annotations

LOW_TRUST_KEYWORDS = (
    "unconfirmed", "indeterminate", "evidence-gap", "no-server-side-fault", "unclassified",
)


def ticket_count(curated_tickets: str | None) -> int:
    if not curated_tickets:
        return 0
    return len([t for t in str(curated_tickets).split(",") if t.strip()])


def root_cause_nature(root_cause_id: str) -> str:
    slug = (root_cause_id or "").split("/", 1)[-1].lower()
    return "unconfirmed" if any(k in slug for k in LOW_TRUST_KEYWORDS) else "confirmed"


def confidence_tier(n_tickets: int, nature: str) -> str:
    if nature == "unconfirmed":
        return "low"          # slug override wins outright
    if n_tickets >= 10:
        return "high"
    if n_tickets >= 3:
        return "medium"
    return "low"
