"""
The ContextualPrecision reference (`expected_output`).

Pure: assembled from answer content only — the correct root cause, the engineer's
root-cause narrative(s) from the source ticket(s), and the observed error signature.
Authoring metadata (`notes`, `intent`) is deliberately excluded: it would either prime
the judge or grade it on how the query was written rather than what a correct match is.

`narratives` is a pre-loaded {ticket_id: root_cause_narrative} dict (read from the
operational store by `adapter/corpus.py`), so this function stays IO-free.
"""

from __future__ import annotations

from ..common.queries import Query


def build_expected_output(query: Query, narratives: dict[str, str]) -> str:
    parts: list[str] = []

    if query.expected_root_cause:
        parts.append(f"Correct root cause: {', '.join(query.expected_root_cause)}")

    # Synthesis queries carry several source tickets; concatenate their narratives on
    # purpose, because the synthesis answer genuinely spans multiple causes.
    if len(query.source_tickets) > 1:
        parts.append(f"This query spans {len(query.source_tickets)} related causes:")
    for tid in query.source_tickets:
        narrative = narratives.get(tid)
        if narrative:
            parts.append(f"- Root cause detail ({tid}): {narrative}")

    if query.error_string:
        parts.append(f"Observed error signature: {query.error_string}")

    return "\n".join(parts)
