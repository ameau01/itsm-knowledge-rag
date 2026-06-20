"""
Relevance oracle.

Builds the ground-truth relevance sets from `catalog.json`. Relevance is *cluster
membership*, per metrics.md:
  - strict  : tickets under the query's expected_root_cause(s)
  - lenient : tickets under the query's expected_family(ies)  (union of the family's
              root-cause clusters)

This is deterministic — exact ticket-id set membership, no LLM, no free text.
"""

from __future__ import annotations

import json
from pathlib import Path

from .queries import Query

STRICT = "strict"
LENIENT = "lenient"


class RelevanceOracle:
    def __init__(
        self,
        root_cause_to_tickets: dict[str, set[str]],
        family_to_tickets: dict[str, set[str]],
        ticket_to_root_cause: dict[str, str],
    ) -> None:
        self._rc = root_cause_to_tickets
        self._fam = family_to_tickets
        self._ticket_rc = ticket_to_root_cause

    # ── construction ────────────────────────────────────────────────────────────
    @classmethod
    def from_catalog(cls, path: str | Path) -> "RelevanceOracle":
        catalog = json.loads(Path(path).read_text())
        rc_to_tickets: dict[str, set[str]] = {}
        fam_to_tickets: dict[str, set[str]] = {}
        ticket_to_rc: dict[str, str] = {}

        for fam in catalog["families"]:
            fam_id = fam["family_id"]
            fam_to_tickets.setdefault(fam_id, set())
            for rc in fam["root_causes"]:
                rc_id = rc["root_cause_id"]
                tickets = set(rc["ticket_ids"])
                rc_to_tickets[rc_id] = tickets
                fam_to_tickets[fam_id] |= tickets
                for t in tickets:
                    ticket_to_rc[t] = rc_id
        return cls(rc_to_tickets, fam_to_tickets, ticket_to_rc)

    # ── queries ─────────────────────────────────────────────────────────────────
    def relevant_tickets(self, query: Query, level: str = STRICT) -> set[str]:
        """Set of relevant ticket-ids for a query at the requested level."""
        if level == STRICT:
            out: set[str] = set()
            for rc_id in query.expected_root_cause:
                out |= self._rc.get(rc_id, set())
            return out
        if level == LENIENT:
            out = set()
            for fam_id in query.expected_family:
                out |= self._fam.get(fam_id, set())
            return out
        raise ValueError(f"unknown relevance level: {level!r}")

    def n_relevant(self, query: Query, level: str = STRICT) -> int:
        return len(self.relevant_tickets(query, level))

    def root_cause_of(self, ticket_id: str) -> str | None:
        """Map a retrieved ticket back to its root cause (for candidate-set metrics)."""
        return self._ticket_rc.get(ticket_id)

    # ── inventory (for sanity tests / mock fillers) ───────────────────────────────
    @property
    def all_ticket_ids(self) -> set[str]:
        out: set[str] = set()
        for tickets in self._rc.values():
            out |= tickets
        return out

    @property
    def root_cause_ids(self) -> set[str]:
        return set(self._rc)

    @property
    def family_ids(self) -> set[str]:
        return set(self._fam)
