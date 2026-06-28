"""Eval case types + source/summary rendering.

The overview's reference is the wiki page (curated_description); the summary is the ai_overview.
`render_source` skips empty fields, so the 5-field curation (no diagnostic_summary) renders cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# curated_description fields the overview is built from = its reference for summarization.
# (diagnostic_summary stays in the list but is skipped when empty — 5-field-safe.)
SOURCE_FIELDS = ["symptoms", "cause", "variations", "diagnostic_summary"]


@dataclass
class OverviewCase:
    root_cause_id: str
    family: str
    confidence: str
    ticket_count: int
    source: str          # rendered curated_description
    summary: str         # rendered ai_overview (lead + key_points)
    lead: str = ""       # the lead alone (for the guard)


@dataclass
class CaseScore:
    root_cause_id: str
    family: str
    confidence: str
    ticket_count: int
    scores: dict = field(default_factory=dict)     # metric -> {score, runs, reason}
    guard: dict = field(default_factory=dict)       # {ok, hard_fail, soft_warn}


def render_source(cd: dict) -> str:
    parts = []
    for f in SOURCE_FIELDS:
        v = (cd.get(f) or "").strip()
        if v:
            parts.append(f"{f.replace('_', ' ').title()}:\n{v}")
    return "\n\n".join(parts)


def render_summary(ao: dict) -> str:
    lead = (ao.get("lead") or "").strip()
    pts = "\n".join(f"- {p}" for p in ao.get("key_points", []) if p)
    return (lead + ("\n\n" + pts if pts else "")).strip()


def case_from_row(row: dict) -> OverviewCase:
    cd, ao = row["curated_description"], row["ai_overview"]
    return OverviewCase(
        root_cause_id=row["root_cause_id"], family=row["family"],
        confidence=ao.get("confidence", "?"), ticket_count=row["ticket_count"],
        source=render_source(cd), summary=render_summary(ao),
        lead=(ao.get("lead") or "").strip(),
    )
